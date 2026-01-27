# Data Persistence Setup

Your app now saves collection data to the Documents directory, which means:
- ✅ Data persists through app deletion/reinstallation (if iCloud Backup is enabled)
- ✅ No special Xcode capabilities required!
- ✅ Works automatically

## How It Works

The app saves data to the **Documents directory**, which:
- Is automatically backed up to iCloud Backup (if enabled in Settings)
- Persists through app updates
- Can be restored when you reinstall the app (if iCloud Backup is enabled)

**No Xcode setup required!** It just works.

## How It Works

- **First launch**: Loads from the bundled JSON file, then saves to Documents
- **Subsequent launches**: Loads from Documents automatically
- **Automatic save**: When you mark figures as "Have" or "Want", it saves immediately
- **Backup**: If iCloud Backup is enabled, your data is automatically backed up

## Enable iCloud Backup (Optional but Recommended)

To ensure your data is backed up and can be restored:

1. **Go to Settings** on your iPhone/iPad
2. **Tap [Your Name] > iCloud**
3. **Tap "iCloud Backup"**
4. **Make sure it's turned ON**

This will automatically back up your app data (including the collection) to iCloud.

## Checking Status

You can see your storage status in the **Stats** tab - it will show where your data is saved.

## Restoring After Reinstall

If you delete and reinstall the app:
1. Make sure iCloud Backup was enabled before deletion
2. After reinstalling, your data will be restored automatically from iCloud Backup
3. The app will load your saved collection on first launch
