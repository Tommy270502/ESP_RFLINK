#include "AppState.h"
#include <string.h>

RadioConfig rfCfg;
PacketStats stats;
String lastErrorCode;
String lastErrorMessage;
EventLog eventLog;

void EventLog::add(const char* type, const char* detail) {
  EventLogEntry& entry = entries[head];
  entry.timestampMs = millis();
  strncpy(entry.type, type, sizeof(entry.type) - 1);
  entry.type[sizeof(entry.type) - 1] = '\0';
  strncpy(entry.detail, detail, sizeof(entry.detail) - 1);
  entry.detail[sizeof(entry.detail) - 1] = '\0';
  head = (head + 1) % EVENT_LOG_CAPACITY;
  if (entryCount < EVENT_LOG_CAPACITY) entryCount++;
}

const EventLogEntry& EventLog::at(size_t index) const {
  size_t start = (entryCount < EVENT_LOG_CAPACITY) ? 0 : head;
  size_t pos = (start + index) % EVENT_LOG_CAPACITY;
  return entries[pos];
}
