# pylint: disable=missing-docstring,line-too-long

from pathlib import Path
import re
import zipfile

from core.enums import ApplicationSettingsEnum
from core.logger import get_logger
from services.notification_service import NotificationService
from services.settings_service import SettingsService


class ZipService:
    def __init__(self, notification_service:NotificationService):
        self.zip_file_path = None
        self.settings_service = SettingsService()
        self.notification_service = notification_service
        self.__logger = get_logger(__name__)

    def create_zip(self, images):
        try:
            work_dir = Path(self.settings_service.get_setting(ApplicationSettingsEnum.WORK_DIR))

            sci = self.settings_service.get_setting(ApplicationSettingsEnum.SCI)
            rc = self.settings_service.get_setting(ApplicationSettingsEnum.RC)

            # Build paths
            rc_path = work_dir.joinpath(rc)
            sci_path = rc_path.joinpath(sci)

            # Extract SCI number
            sci_number = self._extract_sci_number(sci).zfill(4)  # pad with zeros to 4 digits

            # Create zip filename: SCI-xxxx-{RC_name}.zip
            zip_filename = f"SCI-{sci_number}-{rc}.zip"
            zip_path = rc_path / zip_filename

            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for image in images:
                    file_path = image.file_path
                    # facem fisiereele relative la sci path ca sa avem o arhiva frumoasa fara cai absolute
                    arcname = file_path.relative_to(sci_path)
                    zipf.write(file_path, arcname)

            self.__logger.info(f"ZIP file created: {zip_path}")
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.__logger.exception(f"Error creating ZIP: {e}", e)
            raise RuntimeError(e) from e
        else:
            return zip_path

    def _extract_sci_number(self, sci_name: str) -> str:
        """Extract the number from SCI name.

        Examples:
            'SCDX-1234' -> '1234'
            '1234' -> '1234'
            'SCI-0001-ABC' -> '0001'
        """
        # Try to extract any continuous sequence of digits
        match = re.search(r'\d+', sci_name)
        if match:
            return match.group()
        return "0000"
