import pymedia.removable.cd as cd

def readTrack(track, offset, bytes):
  cd.init()
  if cd.getCount() == 0:
    print 'There is no cdrom found. Bailing out...'
    return 0

  c = cd.CD(0)
  props = c.getProperties()
  if props['type'] != 'AudioCD':
    print 'Media in %s has type %s, not AudioCD. Cannot read audio data.' % (c.getName(), props['type'])
    return 0

  tr0 = c.open(props['titles'][track - 1]['name'])
  tr0.seek(offset, cd.SEEK_SET)
  return tr0.read(bytes)