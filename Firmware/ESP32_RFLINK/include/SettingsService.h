#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

class SettingsService {
public:
  void begin();
  bool save();
  bool reset();

  const char* deviceName() const;
  const char* apSsid() const;
  const char* apPass() const;
  const char* bleName() const;

  bool setDeviceName(const String& value);
  bool setApSsid(const String& value);
  bool setApPass(const String& value);
  bool setBleName(const String& value);
  bool setAuthRequired(bool value);
  bool setAuthToken(const String& value);

  bool authRequired() const;
  bool tokenConfigured() const;
  bool checkAuth(const char* token) const;
  bool dirty() const;
  bool rebootRequired() const;
  bool loadedFromNvs() const;
  void markDirty();

  void fillSettings(JsonObject data) const;
  void fillDevice(JsonObject data) const;
  void fillSecurity(JsonObject data) const;
  void fillStorage(JsonObject data) const;

private:
  void applyDefaults();
  bool validName(const String& value, size_t maxLen) const;

  String currentDeviceName;
  String currentApSsid;
  String currentApPass;
  String currentBleName;
  String currentAuthToken;
  bool currentAuthRequired = false;
  bool settingsLoaded = false;
  bool settingsDirty = false;
  bool needsReboot = false;
};

extern SettingsService settingsService;
