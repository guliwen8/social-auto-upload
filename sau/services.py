from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from uploader.bilibili_uploader.runtime import run_biliup_command
from uploader.douyin_uploader.main import (
    DouYinNote,
    DouYinVideo,
    cookie_auth as douyin_cookie_auth,
    douyin_setup,
)
from uploader.ks_uploader.main import (
    KSNote,
    KSVideo,
    cookie_auth as kuaishou_cookie_auth,
    ks_setup,
)
from uploader.tencent_uploader.main import (
    TencentVideo,
    cookie_auth as tencent_cookie_auth,
    tencent_setup,
)
from uploader.xiaohongshu_uploader.main import (
    XiaoHongShuNote,
    XiaoHongShuVideo,
    cookie_auth as xiaohongshu_cookie_auth,
    xiaohongshu_setup,
)
from uploader.youtube_uploader.main import (
    YouTubeVideo,
    cookie_auth as youtube_cookie_auth,
    youtube_setup,
)

from .models import (
    BilibiliVideoUploadRequest,
    DouyinNoteUploadRequest,
    DouyinVideoUploadRequest,
    KuaishouNoteUploadRequest,
    KuaishouVideoUploadRequest,
    TencentVideoUploadRequest,
    XiaohongshuNoteUploadRequest,
    XiaohongshuVideoUploadRequest,
    YouTubeVideoUploadRequest,
)
from .runtime import has_interactive_terminal, resolve_account_file


@dataclass(frozen=True, slots=True)
class PlatformCapabilities:
    supports_login: bool = True
    supports_check: bool = True
    supports_video_upload: bool = False
    supports_note_upload: bool = False
    supports_schedule: bool = False
    supports_headless: bool = True


class BasePlatformAdapter(ABC):
    platform_name: str
    capabilities: PlatformCapabilities

    async def login(self, account_name: str, headless: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    async def check(self, account_name: str) -> bool:
        raise NotImplementedError

    async def upload_video(self, request: Any) -> Path:
        raise RuntimeError(f"{self.platform_name} does not support video upload")

    async def upload_note(self, request: Any) -> Path:
        raise RuntimeError(f"{self.platform_name} does not support note upload")


class DouyinAdapter(BasePlatformAdapter):
    platform_name = "douyin"
    capabilities = PlatformCapabilities(
        supports_video_upload=True,
        supports_note_upload=True,
        supports_schedule=True,
    )

    async def login(self, account_name: str, headless: bool = True) -> dict[str, Any]:
        account_file = resolve_account_file(self.platform_name, account_name)
        return await douyin_setup(str(account_file), handle=True, return_detail=True, headless=headless)

    async def check(self, account_name: str) -> bool:
        account_file = resolve_account_file(self.platform_name, account_name)
        if not account_file.exists():
            return False
        return await douyin_cookie_auth(str(account_file))

    async def upload_video(self, request: DouyinVideoUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await douyin_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Douyin cookie is missing or expired: {account_file}. "
                f"Run `sau douyin login --account {request.account_name}` first."
            )

        app = DouYinVideo(
            request.title,
            str(request.video_file),
            request.tags,
            request.publish_date,
            str(account_file),
            desc=request.description,
            thumbnail_landscape_path=(
                str(request.thumbnail_landscape_file) if request.thumbnail_landscape_file else None
            ),
            thumbnail_portrait_path=(
                str(request.thumbnail_portrait_file or request.thumbnail_file)
                if request.thumbnail_portrait_file or request.thumbnail_file
                else None
            ),
            productLink=request.product_link,
            productTitle=request.product_title,
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
        )
        await app.douyin_upload_video()
        return account_file

    async def upload_note(self, request: DouyinNoteUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await douyin_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Douyin cookie is missing or expired: {account_file}. "
                f"Run `sau douyin login --account {request.account_name}` first."
            )

        app = DouYinNote(
            image_paths=[str(path) for path in request.image_files],
            title=request.title,
            note=request.note,
            tags=request.tags,
            publish_date=request.publish_date,
            account_file=str(account_file),
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
            bgm=request.bgm,
        )
        await app.douyin_upload_note()
        return account_file


class KuaishouAdapter(BasePlatformAdapter):
    platform_name = "kuaishou"
    capabilities = PlatformCapabilities(
        supports_video_upload=True,
        supports_note_upload=True,
        supports_schedule=True,
    )

    async def login(self, account_name: str, headless: bool = True) -> dict[str, Any]:
        account_file = resolve_account_file(self.platform_name, account_name)
        return await ks_setup(str(account_file), handle=True, return_detail=True, headless=headless)

    async def check(self, account_name: str) -> bool:
        account_file = resolve_account_file(self.platform_name, account_name)
        if not account_file.exists():
            return False
        return await kuaishou_cookie_auth(str(account_file))

    async def upload_video(self, request: KuaishouVideoUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await ks_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Kuaishou cookie is missing or expired: {account_file}. "
                f"Run `sau kuaishou login --account {request.account_name}` first."
            )

        app = KSVideo(
            title=request.title,
            file_path=str(request.video_file),
            desc=request.description,
            tags=request.tags,
            publish_date=request.publish_date,
            account_file=str(account_file),
            thumbnail_path=str(request.thumbnail_file) if request.thumbnail_file else None,
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
        )
        await app.main()
        return account_file

    async def upload_note(self, request: KuaishouNoteUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await ks_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Kuaishou cookie is missing or expired: {account_file}. "
                f"Run `sau kuaishou login --account {request.account_name}` first."
            )

        app = KSNote(
            image_paths=[str(path) for path in request.image_files],
            title=request.title,
            note=request.note,
            tags=request.tags,
            publish_date=request.publish_date,
            account_file=str(account_file),
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
        )
        await app.main()
        return account_file


class XiaohongshuAdapter(BasePlatformAdapter):
    platform_name = "xiaohongshu"
    capabilities = PlatformCapabilities(
        supports_video_upload=True,
        supports_note_upload=True,
        supports_schedule=True,
    )

    async def login(self, account_name: str, headless: bool = True) -> dict[str, Any]:
        account_file = resolve_account_file(self.platform_name, account_name)
        return await xiaohongshu_setup(
            str(account_file), handle=True, return_detail=True, headless=headless
        )

    async def check(self, account_name: str) -> bool:
        account_file = resolve_account_file(self.platform_name, account_name)
        if not account_file.exists():
            return False
        return await xiaohongshu_cookie_auth(str(account_file))

    async def upload_video(self, request: XiaohongshuVideoUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await xiaohongshu_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Xiaohongshu cookie is missing or expired: {account_file}. "
                f"Run `sau xiaohongshu login --account {request.account_name}` first."
            )

        app = XiaoHongShuVideo(
            title=request.title,
            file_path=str(request.video_file),
            desc=request.description,
            tags=request.tags,
            publish_date=request.publish_date,
            account_file=str(account_file),
            thumbnail_path=str(request.thumbnail_file) if request.thumbnail_file else None,
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
        )
        await app.main()
        return account_file

    async def upload_note(self, request: XiaohongshuNoteUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await xiaohongshu_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Xiaohongshu cookie is missing or expired: {account_file}. "
                f"Run `sau xiaohongshu login --account {request.account_name}` first."
            )

        app = XiaoHongShuNote(
            image_paths=[str(path) for path in request.image_files],
            title=request.title,
            desc=request.note,
            note=request.note,
            tags=request.tags,
            publish_date=request.publish_date,
            account_file=str(account_file),
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
        )
        await app.main()
        return account_file


class BilibiliAdapter(BasePlatformAdapter):
    platform_name = "bilibili"
    capabilities = PlatformCapabilities(
        supports_video_upload=True,
        supports_schedule=True,
        supports_headless=False,
    )

    async def login(self, account_name: str, headless: bool = True) -> dict[str, Any]:
        del headless
        account_file = resolve_account_file(self.platform_name, account_name)
        if not has_interactive_terminal():
            return {
                "success": False,
                "message": (
                    "Bilibili login requires a local interactive terminal. "
                    f"Please run `sau bilibili login --account {account_name}` yourself in a local terminal. "
                    "If the terminal QR code does not render completely, open `./qrcode.png` and scan that image."
                ),
                "account_file": str(account_file),
            }

        result = run_biliup_command(["-u", str(account_file), "login"], interactive=True)
        success = result.returncode == 0
        message = (result.stderr or result.stdout or "").strip()
        if not message:
            message = "Bilibili login completed" if success else "Bilibili login failed"
        return {
            "success": success,
            "message": message,
            "account_file": str(account_file),
        }

    async def check(self, account_name: str) -> bool:
        account_file = resolve_account_file(self.platform_name, account_name)
        if not account_file.exists():
            return False
        result = run_biliup_command(["-u", str(account_file), "renew"])
        return result.returncode == 0

    async def upload_video(self, request: BilibiliVideoUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        if not account_file.exists():
            raise RuntimeError(
                f"Bilibili account file is missing: {account_file}. "
                f"Run `sau bilibili login --account {request.account_name}` first."
            )

        arguments = [
            "-u",
            str(account_file),
            "upload",
            str(request.video_file),
            "--title",
            request.title,
            "--desc",
            request.description,
            "--tid",
            str(request.tid),
        ]
        if request.tags:
            arguments.extend(["--tag", ",".join(request.tags)])
        if isinstance(request.publish_date, datetime):
            arguments.extend(["--dtime", str(int(request.publish_date.timestamp()))])

        result = run_biliup_command(arguments)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "").strip() or "Bilibili upload failed")
        return account_file


class TencentAdapter(BasePlatformAdapter):
    platform_name = "tencent"
    capabilities = PlatformCapabilities(
        supports_video_upload=True,
        supports_schedule=True,
    )

    async def login(self, account_name: str, headless: bool = True) -> dict[str, Any]:
        account_file = resolve_account_file(self.platform_name, account_name)
        return await tencent_setup(str(account_file), handle=True, return_detail=True, headless=headless)

    async def check(self, account_name: str) -> bool:
        account_file = resolve_account_file(self.platform_name, account_name)
        if not account_file.exists():
            return False
        return await tencent_cookie_auth(str(account_file))

    async def upload_video(self, request: TencentVideoUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await tencent_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"Tencent/WeChat Channels cookie is missing or expired: {account_file}. "
                f"Run `sau tencent login --account {request.account_name}` first."
            )

        app = TencentVideo(
            title=request.title,
            file_path=str(request.video_file),
            tags=request.tags,
            publish_date=request.publish_date,
            account_file=str(account_file),
            category=request.category,
            is_draft=request.is_draft,
            desc=request.description,
            thumbnail_path=str(request.thumbnail_file) if request.thumbnail_file else None,
            thumbnail_landscape_path=(
                str(request.thumbnail_landscape_file) if request.thumbnail_landscape_file else None
            ),
            thumbnail_portrait_path=(
                str(request.thumbnail_portrait_file) if request.thumbnail_portrait_file else None
            ),
            short_title=request.short_title,
            publish_strategy=request.publish_strategy,
            debug=request.debug,
            headless=request.headless,
        )
        await app.tencent_upload_video()
        return account_file


class YouTubeAdapter(BasePlatformAdapter):
    platform_name = "youtube"
    capabilities = PlatformCapabilities(
        supports_video_upload=True,
        supports_headless=False,
    )

    async def login(self, account_name: str, headless: bool = False) -> dict[str, Any]:
        account_file = resolve_account_file(self.platform_name, account_name)
        return await youtube_setup(str(account_file), handle=True, return_detail=True, headless=headless)

    async def check(self, account_name: str) -> bool:
        account_file = resolve_account_file(self.platform_name, account_name)
        if not account_file.exists():
            return False
        return await youtube_cookie_auth(str(account_file))

    async def upload_video(self, request: YouTubeVideoUploadRequest) -> Path:
        account_file = resolve_account_file(self.platform_name, request.account_name)
        is_ready = await youtube_setup(str(account_file), handle=False)
        if not is_ready:
            raise RuntimeError(
                f"YouTube cookie is missing or expired: {account_file}. "
                f"Run `sau youtube login --account {request.account_name}` first."
            )

        app = YouTubeVideo(
            request.title,
            str(request.video_file),
            request.tags,
            str(account_file),
            description=request.description,
            thumbnail_path=str(request.thumbnail_file) if request.thumbnail_file else None,
            playlist=request.playlist,
            visibility=request.visibility,
            debug=request.debug,
            headless=request.headless,
        )
        await app.main()
        return account_file


PLATFORM_ADAPTERS: dict[str, BasePlatformAdapter] = {
    "douyin": DouyinAdapter(),
    "kuaishou": KuaishouAdapter(),
    "xiaohongshu": XiaohongshuAdapter(),
    "bilibili": BilibiliAdapter(),
    "tencent": TencentAdapter(),
    "youtube": YouTubeAdapter(),
}


def get_platform_adapter(platform: str) -> BasePlatformAdapter:
    try:
        return PLATFORM_ADAPTERS[platform]
    except KeyError as exc:
        raise RuntimeError(f"Unsupported platform: {platform}") from exc


class SocialAutoUploadService:
    async def login(self, platform: str, account_name: str, headless: bool = True) -> dict[str, Any]:
        return await get_platform_adapter(platform).login(account_name=account_name, headless=headless)

    async def check(self, platform: str, account_name: str) -> bool:
        return await get_platform_adapter(platform).check(account_name=account_name)

    async def upload_video(self, platform: str, request: Any) -> Path:
        return await get_platform_adapter(platform).upload_video(request)

    async def upload_note(self, platform: str, request: Any) -> Path:
        return await get_platform_adapter(platform).upload_note(request)

    def get_capabilities(self, platform: str) -> PlatformCapabilities:
        return get_platform_adapter(platform).capabilities


service = SocialAutoUploadService()


async def login_douyin_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    return await service.login("douyin", account_name, headless=headless)


async def check_douyin_account(account_name: str) -> bool:
    return await service.check("douyin", account_name)


async def upload_douyin_video(request: DouyinVideoUploadRequest) -> Path:
    return await service.upload_video("douyin", request)


async def upload_douyin_note(request: DouyinNoteUploadRequest) -> Path:
    return await service.upload_note("douyin", request)


async def login_kuaishou_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    return await service.login("kuaishou", account_name, headless=headless)


async def check_kuaishou_account(account_name: str) -> bool:
    return await service.check("kuaishou", account_name)


async def upload_kuaishou_video(request: KuaishouVideoUploadRequest) -> Path:
    return await service.upload_video("kuaishou", request)


async def upload_kuaishou_note(request: KuaishouNoteUploadRequest) -> Path:
    return await service.upload_note("kuaishou", request)


async def login_xiaohongshu_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    return await service.login("xiaohongshu", account_name, headless=headless)


async def check_xiaohongshu_account(account_name: str) -> bool:
    return await service.check("xiaohongshu", account_name)


async def upload_xiaohongshu_video(request: XiaohongshuVideoUploadRequest) -> Path:
    return await service.upload_video("xiaohongshu", request)


async def upload_xiaohongshu_note(request: XiaohongshuNoteUploadRequest) -> Path:
    return await service.upload_note("xiaohongshu", request)


async def login_bilibili_account(account_name: str) -> dict[str, Any]:
    return await service.login("bilibili", account_name, headless=True)


async def check_bilibili_account(account_name: str) -> bool:
    return await service.check("bilibili", account_name)


async def upload_bilibili_video(request: BilibiliVideoUploadRequest) -> Path:
    return await service.upload_video("bilibili", request)


async def login_tencent_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    return await service.login("tencent", account_name, headless=headless)


async def check_tencent_account(account_name: str) -> bool:
    return await service.check("tencent", account_name)


async def upload_tencent_video(request: TencentVideoUploadRequest) -> Path:
    return await service.upload_video("tencent", request)


async def login_youtube_account(account_name: str, headless: bool = False) -> dict[str, Any]:
    return await service.login("youtube", account_name, headless=headless)


async def check_youtube_account(account_name: str) -> bool:
    return await service.check("youtube", account_name)


async def upload_youtube_video(request: YouTubeVideoUploadRequest) -> Path:
    return await service.upload_video("youtube", request)
