import glob
from PIL import Image
import concurrent.futures

def conv(name):
  i, name = name
  if i%100 == 0:
    print("now iter", i)
  target_size = (224,224)
  img = Image.open(name)
  w, h = img.size
  if w/h > 1.5:
    return 
  if w/h < 0.75:
    return
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
    #print(bx)
    blank.paste(img, (bx, 0) )
  sname = name.split("/").pop().replace(".jpg", "")
  blank.save("minimize224/mini.{}.png".format(sname))
  #blank = blank.resize( target_size )

def main():
  names = [(i,name) for i, name in enumerate(glob.glob("imgs/*"))]
  for n in names[:100]:
    conv(n)
  with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
    executor.map(conv, names)

if __name__ == '__main__': 
  main()
