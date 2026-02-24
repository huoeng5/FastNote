import tempfile
from pathlib import Path

from PIL import Image

from DesktopAssistant.database.image_manager import ImageManager


class TestImageManager:
    def setup_method(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.manager = ImageManager(base_dir=self.base_dir)

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_save_image_returns_relative_path(self):
        image = Image.new('RGB', (20, 20), color='red')

        relative_path = self.manager.save_image(image)
        assert relative_path.startswith('images/')

        absolute_path = self.manager.get_absolute_path(relative_path)
        assert absolute_path.exists()

    def test_saved_file_name_is_unique(self):
        image = Image.new('RGB', (10, 10), color='blue')

        path1 = self.manager.save_image(image)
        path2 = self.manager.save_image(image)

        assert path1 != path2
