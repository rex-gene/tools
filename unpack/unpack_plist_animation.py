#!python  
import os,sys  
from xml.etree import ElementTree  
from PIL import Image  
  
def tree_to_dict(tree):  
    d = {}  
    for index, item in enumerate(tree):  
        if item.tag == 'key':
            if tree[index+1].tag == 'string':  
                d[item.text] = tree[index + 1].text  
            elif tree[index + 1].tag == 'true':  
                d[item.text] = True  
            elif tree[index + 1].tag == 'false':  
                d[item.text] = False  
            elif tree[index + 1].tag == 'integer':
                d[item.text] = tree[index + 1].text
            elif tree[index + 1].tag == 'real':
                d[item.text] = tree[index + 1].text
            elif tree[index+1].tag == 'dict':  
                d[item.text] = tree_to_dict(tree[index+1])  
    return d  
  
def gen_png_from_plist(plist_filename, png_filename):  
    file_path = plist_filename.replace('.plist', '')  
    big_image = Image.open(png_filename)  
    root = ElementTree.fromstring(open(plist_filename, 'r').read())  
    plist_dict = tree_to_dict(root[0])  
    for k,v in plist_dict['frames'].items():
        x = float(v['x'])
        y = float(v['y'])

        #offsetX = int(float(v['offsetX']))
        #offsetY = int(float(v['offsetY']))
    
        #x = x + offsetX
        #y = y + offsetY
        
        width = int(v['width'])
        height = int(v['height'])

        box=(   
            int(x),
            int(y),
            int(x + width),  
            int(y + height),  
            )  
        sourceWidth = int(v['originalWidth'])
        sourceHeigt = int(v['originalHeight'])
        
        sizelist = []
        sizelist.append(int(sourceWidth))
        sizelist.append(int(sourceHeigt))

        rect_on_big = big_image.crop(box)  
  
        result_image = Image.new('RGBA', sizelist, (0,0,0,0))  
        result_box=(  
            ( sourceWidth - width )/2,  
            ( sourceHeigt - height )/2,  
            ( sourceWidth + width )/2,  
            ( sourceHeigt + height )/2  
            )  

        result_image.paste(rect_on_big, result_box, mask=0)  
  
        if not os.path.isdir(file_path):  
            os.mkdir(file_path)  

        dirlist = k.split("/")
        outfile = file_path
        l = len(dirlist) - 1
        for i in range(0, l) :
            outfile = outfile + "/" + dirlist[i] 
            if not os.path.isdir(outfile):
                os.mkdir(outfile)
        
        outfile = outfile + "/" + dirlist[l]
        #outfile = (file_path+'/' + k).replace('gift_', '')  
        result_image.save(outfile)  
  
if __name__ == '__main__':  
    filename = sys.argv[1]  
    plist_filename = filename + '.plist'  
    png_filename = filename + '.png' 
    plist_filename = os.path.abspath(plist_filename)  
    png_filename = os.path.abspath(png_filename)
    print "====star===="    
    print plist_filename
    print png_filename 
    print os.path.abspath(plist_filename)
    print "====end===="    
    if (os.path.exists(plist_filename) and os.path.exists(png_filename)):  
        gen_png_from_plist( plist_filename, png_filename )  
    else:  
        print "make sure you have boith plist and png files in the same directory"  
