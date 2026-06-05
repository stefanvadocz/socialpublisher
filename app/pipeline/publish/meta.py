"""Meta (Facebook Page + Instagram) publisher.

STUBBED for the MVP. The control flow for the real Graph API calls is sketched
below but guarded so it is never invoked until ``PUBLISHER=meta`` and the
credentials are configured. Going live requires:

  * A Facebook **Page** and a long-lived **Page access token**.
  * An **Instagram Business/Creator account** linked to that Page.
  * A Meta App approved (App Review) for: ``pages_manage_posts``,
    ``pages_read_engagement``, ``instagram_basic``, ``instagram_content_publish``.
  * A publicly reachable ``image_url`` (Instagram fetches it server-side).

Facebook photo post:  POST /{page-id}/photos   (url, caption, access_token)
Instagram (two-step): POST /{ig-user-id}/media          (image_url, caption)
                      POST /{ig-user-id}/media_publish  (creation_id)
"""

from __future__ import annotations

import logging

import httpx

from app.config import Settings
from app.enums import Platform
from app.pipeline.publish.base import Publisher, PublishResult

logger = logging.getLogger(__name__)


class MetaPublisher(Publisher):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = f"https://graph.facebook.com/{settings.meta_graph_version}"

    def _require_config(self) -> None:
        s = self.settings
        missing = [
            name
            for name, val in (
                ("META_PAGE_ID", s.meta_page_id),
                ("META_PAGE_ACCESS_TOKEN", s.meta_page_access_token),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(
                "MetaPublisher is not configured: missing " + ", ".join(missing)
            )

    def publish(
        self, *, caption: str, image_url: str, targets: list[Platform]
    ) -> dict[Platform, PublishResult]:
        self._require_config()
        results: dict[Platform, PublishResult] = {}
        with httpx.Client(timeout=60.0) as client:
            for platform in targets:
                try:
                    if platform is Platform.FACEBOOK:
                        results[platform] = self._publish_facebook(client, caption, image_url)
                    elif platform is Platform.INSTAGRAM:
                        results[platform] = self._publish_instagram(client, caption, image_url)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Meta publish failed for %s", platform)
                    results[platform] = PublishResult(ok=False, error=str(exc))
        return results

    def _publish_facebook(
        self, client: httpx.Client, caption: str, image_url: str
    ) -> PublishResult:
        s = self.settings
        resp = client.post(
            f"{self.base}/{s.meta_page_id}/photos",
            data={"url": image_url, "caption": caption, "access_token": s.meta_page_access_token},
        )
        resp.raise_for_status()
        post_id = resp.json().get("post_id") or resp.json().get("id")
        return PublishResult(ok=True, external_post_id=post_id)

    def _publish_instagram(
        self, client: httpx.Client, caption: str, image_url: str
    ) -> PublishResult:
        s = self.settings
        if not s.meta_ig_user_id:
            raise RuntimeError("META_IG_USER_ID is required for Instagram publishing")
        # Step 1: create a media container.
        create = client.post(
            f"{self.base}/{s.meta_ig_user_id}/media",
            data={"image_url": image_url, "caption": caption, "access_token": s.meta_page_access_token},
        )
        create.raise_for_status()
        creation_id = create.json()["id"]
        # Step 2: publish the container.
        publish = client.post(
            f"{self.base}/{s.meta_ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": s.meta_page_access_token},
        )
        publish.raise_for_status()
        return PublishResult(ok=True, external_post_id=publish.json().get("id"))
