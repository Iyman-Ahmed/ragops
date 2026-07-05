# Meridian Platform — Storage & Regions

By default, workspace data is stored in the us-east-1 region. Starter workspaces cannot
change their region. Team and Enterprise workspaces may select eu-west-1 or ap-south-1 at
creation time; the region cannot be changed after a workspace is created.

All data is encrypted at rest with AES-256. Data in transit is encrypted with TLS 1.3.
Encryption keys are rotated automatically every 90 days. Enterprise workspaces may supply
their own customer-managed key through the key-management settings.

Managed storage is replicated across three availability zones within the selected region.
Backups are taken every 6 hours and retained for 35 days. A point-in-time restore can
recover a workspace to any moment within the retention window.

Cross-region replication is available on Enterprise only and adds a secondary copy in a
region of your choice. Cross-region replication does not change the primary region used
for reads and writes.
