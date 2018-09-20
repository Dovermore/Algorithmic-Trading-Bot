from datetime import datetime, timezone
import pytz

tz = pytz.timezone("Australia/Melbourne")

now = datetime.now(tz)

timezone.utc

print(now)
print(timezone.utc)