"""Open a level by id, including archived ones hidden from the main list, and wait until it is loaded."""
def open_level(pg, lid, wait=100):
  pg.evaluate(
    """id=>new Promise((resolve,reject)=>{
      const i=LEVELS.findIndex(l=>l.id===id);
      if(i<0){reject(new Error('no level '+id));return}
      load(i,()=>resolve());
    })""",
    lid,
  )
  pg.wait_for_function(
    "id=>!!(typeof L!=='undefined'&&L&&L.id===id&&L.loaded&&L.pieces&&document.body.classList.contains('playing'))",
    arg=lid,
    timeout=20000,
  )
  if wait:
    pg.wait_for_timeout(wait)
