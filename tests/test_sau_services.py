import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sau.runtime import resolve_account_file
from sau.services import (
    PLATFORM_ADAPTERS,
    SocialAutoUploadService,
    get_platform_adapter,
)


class RuntimeTests(unittest.TestCase):
    def test_resolve_account_file_uses_cookies_directory(self):
        account_file = resolve_account_file("douyin", "creator")
        self.assertEqual(account_file.name, "douyin_creator.json")
        self.assertEqual(account_file.parent.name, "cookies")
        self.assertIsInstance(account_file, Path)


class PlatformAdapterTests(unittest.TestCase):
    def test_get_platform_adapter_returns_registered_adapter(self):
        adapter = get_platform_adapter("douyin")
        self.assertIs(adapter, PLATFORM_ADAPTERS["douyin"])
        self.assertTrue(adapter.capabilities.supports_video_upload)
        self.assertTrue(adapter.capabilities.supports_note_upload)


class PlatformAdapterAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_delegates_check_to_platform_adapter(self):
        service = SocialAutoUploadService()
        with patch.object(
            PLATFORM_ADAPTERS["xiaohongshu"],
            "check",
            new=AsyncMock(return_value=True),
        ) as mock_check:
            result = await service.check("xiaohongshu", "creator")

        self.assertTrue(result)
        mock_check.assert_awaited_once_with(account_name="creator")
