from galicaster.core import context

repo = context.get_repository()
for key,mp in repo.iteritems():
    
    if not mp.operation["ingest"] and mp.status>5:
        mp.setOpStatus("ingest",mp.status-4)
        mp.status=4
    mp.getOpStatus("ingest")
    mp.getOpStatus("exporttozip")
    mp.getOpStatus("sidebyside")
    repo.update(mp)
