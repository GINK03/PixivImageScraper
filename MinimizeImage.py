import glob
from PIL import Image

def conv(name):
  target_size = (168,168)
  img = Image.open(name)
  w, h = img.size
  if w > h :
    blank     = Image.new('RGB', target_size)
    shrinkage = (int(w*target_size[0]/w), int(h*target_size[1]/w) )
    img = img.resize(shrinkage)
    bh  = target_size[1]//2 - int(h*target_size[1]/w)//2
    blank.paste(img, (0, bh) )
  if w <= h :
    blank = Image.new('RGB', target_size)
    shrinkage = (int(w*target_size[0]/h), int(h*target_size[1]/h) )
    img = img.resize(shrinkage)
    bx  = target_size[1]//2 - int(w*target_size[1]/h)//2
    print(bx)
    blank.paste(img, (bx, 0) )
  sname = name.split("/").pop().replace(".jpg", "")
  blank.save("minimize/mini.{}.png".format(sname))
  #blank = blank.resize( target_size )

def main():
  names = [name for name in glob.glob("imgs/*")]
  for n in names[:100]:
    conv(n)

if __name__ == '__main__': 
  main()
