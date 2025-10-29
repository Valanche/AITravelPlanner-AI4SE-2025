import os
import logging
import json
from aip import AipSpeech

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, app_id, api_key, secret_key, audio_file):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self.audio_file = audio_file
        self.result_text = ""

    def run(self):
        try:
            logger.info(f"[STT Debug] Initializing AipSpeech client with APP_ID: {self.app_id}")
            client = AipSpeech(self.app_id, self.api_key, self.secret_key)

            logger.info(f"[STT Debug] Opening audio file: {self.audio_file}")
            
            with open(self.audio_file, 'rb') as fp:
                audio_data = fp.read()

            logger.info("[STT Debug] Starting transcription with Baidu ASR...")
            # Assuming the client-side now sends PCM data directly, so format is 'pcm'
            result = client.asr(audio_data, 'pcm', 16000, { 'dev_pid': 1537 }) # 1537 is for Mandarin

            logger.info(f"[STT Debug] Received raw result: {result}")

            if result.get('err_no') == 0 and 'result' in result:
                self.result_text = "".join(result['result'])
            else:
                error_msg = result.get('err_msg', 'Unknown error')
                logger.error(f"[STT Error] Baidu ASR failed: {error_msg}")
                raise Exception(f"Baidu ASR failed: {error_msg}")

            logger.info("[STT Debug] Transcription finished.")
            return self.result_text

        except Exception as e:
            logger.error(f"[STT Error] Transcription failed: {str(e)}")
            raise
        finally:
            # Clean up the temporary file
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)