import os
import json

class SettingsManager:
    @staticmethod
    def load_option(option_name):
        settings = SettingsManager.load_settings()
        return settings.get(option_name)

    @staticmethod
    def load_settings():
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                try:
                    return json.load(f)
                except json.decoder.JSONDecodeError:
                    # Se il file è vuoto o non è JSON valido, restituisci un dizionario vuoto
                    return {}
        else:
            return {}