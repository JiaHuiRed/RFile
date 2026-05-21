#author Red
#260518 JiaHuiRed RFile V0.1.0 — macOS 风格文件管理器
import tkinter as tk
from tkinter import ttk
import ctypes, ctypes.wintypes as w, os, subprocess, datetime, shutil, json
from PIL import Image, ImageDraw, ImageFilter, ImageGrab, ImageTk, ImageFont

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass

VERSION="V0.2.0";W=1200;H=810;MIN_W=800;MIN_H=500;RM=15;SW=255
SW_MIN=100;SW_MAX=400;GC="#020202"

THEMES=[
    {"n":"深蓝","bg":"#13131f","fg":"#e8e8f4","bb":"#1e1e2a","sb":"#13131f","sf":"#ccccdd",
     "sl":"#13131f","ft":"#55556a","pb":"#1a1a2e","pf":"#e8e8f4","bn":"#8888aa",
     "sa":"#1a1a3a","sh":"#3a3a5a","sel":"#2a2a5a","fh":"#1e1e2a","ff":"#8888aa","tc":0x801f1313},
    {"n":"护眼绿","bg":"#c7edcc","fg":"#1a3320","bb":"#b8e4be","sb":"#b8e4be","sf":"#1a3320",
     "sl":"#c7edcc","ft":"#4a7055","pb":"#d8f2db","pf":"#1a3320","bn":"#2d7a3a",
     "sa":"#a0d8a8","sh":"#6aaa6a","sel":"#8ac88a","fh":"#b8e4be","ff":"#2d7a3a","tc":0x80ccedc7},
    {"n":"暖黄","bg":"#f5e6c8","fg":"#3d2e1a","bb":"#ecdbb8","sb":"#ecdbb8","sf":"#3d2e1a",
     "sl":"#f5e6c8","ft":"#8a7a5a","pb":"#faf0dc","pf":"#3d2e1a","bn":"#8a6a30",
     "sa":"#e0ccaa","sh":"#c0a080","sel":"#d0b890","fh":"#ecdbb8","ff":"#8a6a30","tc":0x80c8e6f5},
    {"n":"日间","bg":"#f2f2f7","fg":"#1c1c1e","bb":"#f0f0f0","sb":"#f5f5f5","sf":"#333333",
     "sl":"#f2f2f7","ft":"#8e8e93","pb":"#f8f8f8","pf":"#1c1c1e","bn":"#007aff",
     "sa":"#e0e0e0","sh":"#cccccc","sel":"#c8c8c8","fh":"#f0f0f0","ff":"#555555","tc":0x80f7f2f2},
]
TN=["🌙","🌿","🌞","☀"]

def drives():
    r=[];b=ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if b&(1<<i):
            l=chr(65+i)+":\\";b2=ctypes.create_unicode_buffer(260)
            ctypes.windll.kernel32.GetVolumeInformationW(l,b2,260,None,None,None,None,0)
            r.append((l,b2.value.strip()))
    return r

def fs(n):
    if n<1024:return f"{n}B"
    if n<1024**2:return f"{n/1024:.1f}KB"
    if n<1024**3:return f"{n/1024**2:.1f}MB"
    return f"{n/1024**3:.2f}GB"

def fd(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")if t else""

def fi(n,d):
    if d:return"📁"
    e=os.path.splitext(n)[1].lower()
    return{".txt":"📄",".md":"📄",".py":"🐍",".jpg":"🖼",".png":"🖼",
        ".gif":"🖼",".mp3":"🎵",".mp4":"🎬",".mkv":"🎬",".zip":"📦",
        ".rar":"📦",".7z":"📦",".pdf":"📕",".doc":"📘",".docx":"📘",
        ".xls":"📊",".xlsx":"📊",".exe":"⚙",".lnk":"🔗",
        ".html":"🌐",".json":"📋",".xml":"📋",".ico":"🎯"}.get(e,"📄")

def ft(n):
    e=os.path.splitext(n)[1].lower()
    return{".txt":"文本",".md":"Markdown",".py":"Python",".jpg":"图片",".png":"图片",
        ".gif":"图片",".mp3":"音频",".mp4":"视频",".mkv":"视频",".zip":"压缩包",
        ".rar":"压缩包",".7z":"压缩包",".pdf":"PDF",".doc":"Word",".docx":"Word",
        ".xls":"Excel",".xlsx":"Excel",".exe":"应用",".lnk":"快捷方式",
        ".html":"网页",".json":"JSON",".xml":"XML",".ico":"图标",
        ".svg":"矢量图",".dll":"DLL"}.get(e,"文件")

def openf(p):
    try:os.startfile(p)
    except:
        try:subprocess.Popen(["explorer",p])
        except:pass


class RFile:
    def __init__(self):
        self.root=tk.Tk()
        self.root.withdraw()  # 启动时隐藏，先截屏再显示，消除毛玻璃首帧闪烁
        self.root.title("RFile")
        self._set_app_icon()
        self.ti=2;self._t=THEMES[2];self.root.configure(bg=self._t["bg"])
        sw=self.root.winfo_screenwidth();sh=self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self._freq_path=os.path.join(os.environ.get("APPDATA",""),".rfile","freq.json")
        os.makedirs(os.path.dirname(self._freq_path),exist_ok=True)
        try:
            with open(self._freq_path,encoding="utf-8")as f:self._freq=json.load(f)
        except:self._freq={}
        self.cp=os.path.expanduser("~");self.hist=[];self.hp=-1
        self.sc="name";self.sa=True;self._rd={};self._wd={};self._sash_d={};self._rm=None
        # 260518 Red 初始化剪切板操作标记，防止未复制直接粘贴触发 AttributeError
        self._ip={};self._sh=False;self._clip_cut=False
        self._hwnd=None;self._phwnd=None
        self._sd_photo=None;self._sd_blur_raw=None
        self._tabs=[{"path":self.cp,"hist":[],"hp":-1}];self._active_tab=0
        self._bc_edit=False;self._ql_win=None
        self.style=ttk.Style();self.style.theme_use("clam")
        # 260518 Red 默认启动主题改为暖黄（index 2）
        self._build_ui();self._apply(2);self._nav(self.cp)

        # 260518 Red 右键菜单改用当前主题色，不再硬编码深蓝
        t0=self._t
        self.cmenu=tk.Menu(self.root,tearoff=0,bg=t0["bb"],fg=t0["fg"],
            activebackground=t0["sel"],activeforeground=t0["fg"],borderwidth=0)
        self.cmenu.add_command(label="打开",command=self._cm_open)
        self.cmenu.add_command(label="打开方式...",command=self._cm_openwith)
        self.cmenu.add_separator()
        self.cmenu.add_command(label="新建文件夹 (Ctrl+Shift+N)",command=self._cm_newfolder)
        self.cmenu.add_separator()
        self.cmenu.add_command(label="复制 (Ctrl+C)",command=self._cm_copy)
        self.cmenu.add_command(label="剪切 (Ctrl+X)",command=self._cm_cut)
        self.cmenu.add_command(label="粘贴 (Ctrl+V)",command=self._cm_paste)
        self.cmenu.add_separator()
        self.cmenu.add_command(label="移动到...",command=self._cm_move)
        self.cmenu.add_separator()
        self.cmenu.add_command(label="重命名 (F2)",command=self._cm_rename)
        self.cmenu.add_command(label="删除 (Del)",command=self._cm_delete)
        self.cmenu.add_separator()
        self.cmenu.add_command(label="属性",command=self._cm_properties)
        self.cmenu.add_separator()
        self.cmenu.add_command(label="显示隐藏文件",command=self._cm_hidden)
        self._hidden_idx=self.cmenu.index("end")

        self._iconified=False
        self.root.bind("<KeyPress>",self.on_key)
        self.root.bind("<Map>",self._on_map)
        self.root.bind("<Unmap>",self._on_unmap)
        self.tree.bind("<Button-3>",self._cm_show)
        self.root.bind("<Button-1>",self._click)
        self.root.bind("<B1-Motion>",self._drag)
        self.root.bind("<ButtonRelease-1>",self._rel)
        self.root.bind("<Motion>",self._move)
        # 截屏模糊后再显示窗口，无闪烁
        self.root.update_idletasks()
        self._refresh_glass()
        self._setup_hwnd()  # 在 deiconify 之前去掉标题栏，避免闪烁
        self.root.deiconify()

    # ── 应用主题 ──
    def _apply(self,ti):
        self.ti=ti;self._t=THEMES[ti];t=self._t
        self.root.configure(bg=t["bg"])
        self.bar.configure(bg=t["bb"])
        # 更新顶部栏 Canvas 文字按钮颜色
        for bname,(bg_id,txt_id,hit_id) in self._bar_btns.items():
            self.bar.itemconfig(txt_id,fill=t["bn"])
        self.bar.itemconfig(self._bar_btns["theme"][1],text=TN[ti])
        self.pe.configure(bg=t["pb"],fg=t["pf"],insertbackground=t["fg"])
        self.sd.configure(bg=t["sb"])
        self._sb()
        self._apply_glass_tint()
        self._apply_bar_glass_tint()
        self._ub()
        if hasattr(self,"cmenu"):
            self.cmenu.configure(bg=t["bb"],fg=t["fg"],
                activebackground=t["sel"],activeforeground=t["fg"])
        self.sash.configure(bg=t["sh"])
        self.mn.configure(bg=t["sl"])
        self.ft.configure(bg=t["bg"])
        self.fl.configure(bg=t["bg"],fg=t["ft"])
        self.style.configure("Treeview",bg=t["sl"],fg=t["fg"],fieldbackground=t["sl"],
            rowheight=30,font=("Segoe UI",10),borderwidth=0)
        self.style.map("Treeview",background=[("selected",t["sel"])],
            foreground=[("selected",t["fg"])])
        self.style.configure("Treeview.Heading",bg=t["fh"],fg=t["ff"],
            font=("Segoe UI",9,"bold"),borderwidth=0,relief="flat")
        self.style.map("Treeview.Heading",background=[("active",t["sa"])])
        if hasattr(self,"tabs_bar"):
            self.tabs_bar.configure(bg=t["bg"]);self._draw_tabs()
        if hasattr(self,"_bc_edit") and not self._bc_edit:self._update_bc()

    def _set_app_icon(self):
        try:
            s=64;bg=Image.new("RGBA",(s,s))
            bd=ImageDraw.Draw(bg)
            c1=(0x2d,0x5b,0xe3);c2=(0x0e,0x1a,0x5e)
            for y in range(s):
                t=y/max(1,s-1)
                bd.line([(0,y),(s,y)],fill=(
                    int(c1[0]+(c2[0]-c1[0])*t),
                    int(c1[1]+(c2[1]-c1[1])*t),
                    int(c1[2]+(c2[2]-c1[2])*t),255))
            rad=s//5
            mask=Image.new("L",(s,s),0)
            ImageDraw.Draw(mask).rounded_rectangle([0,0,s-1,s-1],radius=rad,fill=255)
            bg.putalpha(mask)
            img=Image.new("RGBA",(s,s),(0,0,0,0));img.alpha_composite(bg)
            d=ImageDraw.Draw(img)
            font=None
            for fp in["C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/calibrib.ttf"]:
                try:font=ImageFont.truetype(fp,int(s*0.58));break
                except:pass
            if not font:font=ImageFont.load_default()
            bb=d.textbbox((0,0),"R",font=font)
            d.text(((s-(bb[2]-bb[0]))//2-bb[0],(s-(bb[3]-bb[1]))//2-bb[1]),
                "R",fill=(255,255,255,255),font=font)
            self._icon_photo=ImageTk.PhotoImage(img)
            self.root.iconphoto(True,self._icon_photo)
            # 保存临时 .ico，供 _setup_hwnd 通过 WM_SETICON 设置任务栏图标
            import tempfile
            self._ico_path=os.path.join(tempfile.gettempdir(),"_rfile_icon.ico")
            img.save(self._ico_path,format="ICO",sizes=[(32,32),(48,48),(64,64)])
        except:pass

    def _setup_hwnd(self):
        try:
            content=self.root.winfo_id()
            u32=ctypes.windll.user32
            # wrapper 是含标题栏的外层窗口（GetParent 拿父窗口）
            # 无 overrideredirect 时：content 是子窗口，wrapper 是带标题栏的父
            wrapper=u32.GetParent(content) or content
            self._hwnd=wrapper
            # WS_POPUP|WS_SYSMENU|WS_MINIMIZEBOX：无边框，WS_MINIMIZEBOX 使任务栏点击发送 SC_MINIMIZE
            u32.SetWindowLongW(wrapper,-16,0x80000000|0x00080000|0x00020000|0x04000000|0x02000000)
            # WS_EX_APPWINDOW：强制任务栏按钮；移除 WS_EX_TOOLWINDOW
            ex=u32.GetWindowLongW(wrapper,-20)
            u32.SetWindowLongW(wrapper,-20,(ex&~0x80)|0x40000)
            # SWP_FRAMECHANGED 强制立刻应用新样式
            u32.SetWindowPos(wrapper,None,0,0,0,0,0x0001|0x0002|0x0004|0x0020)
            # WM_SETICON 设置任务栏图标（restype=c_void_p 避免 64-bit handle 截断）
            if hasattr(self,"_ico_path") and os.path.exists(self._ico_path):
                u32.LoadImageW.restype=ctypes.c_void_p
                hIcon=u32.LoadImageW(None,self._ico_path,1,0,0,0x10|0x40)
                if hIcon:
                    for h in filter(None,{wrapper,content}):
                        u32.SendMessageW(h,0x0080,0,hIcon)
                        u32.SendMessageW(h,0x0080,1,hIcon)
        except:pass

# ── UI 构建 ──
    def _build_ui(self):
        t=self._t
        self._build_bar()
        self._build_tabs_bar()

        self.bd=tk.Frame(self.root,bg=t["bg"]);self.bd.pack(fill="both",expand=True)
        # 侧边栏改为 Canvas，支持毛玻璃截图贴图
        self.sd=tk.Canvas(self.bd,width=SW,highlightthickness=0,bg=t["sb"])
        self.sd.pack(side="left",fill="y")
        self._sd_bg_id=self.sd.create_image(0,0,anchor="nw")
        self.sd.bind("<Configure>",self._sd_on_configure)
        self._sb()
        self.sash=tk.Frame(self.bd,bg=t["sh"],width=6,cursor="sb_h_double_arrow")
        self.sash.pack(side="left",fill="y")
        self.sash.bind("<Button-1>",self._sash_start)
        self.sash.bind("<B1-Motion>",self._sash_drag)

        self.mn=tk.Frame(self.bd,bg=t["sl"]);self.mn.pack(side="left",fill="both",expand=True)
        self.tree=ttk.Treeview(self.mn,columns=("size","type","modified"),
            displaycolumns=("size","type","modified"),show="tree headings",
            selectmode="browse",style="Treeview")
        self.tree.heading("#0",text="名称",anchor="w",command=lambda:self._sort("name"))
        self.tree.column("#0",width=300,minwidth=120,stretch=True)
        for k,w in[("size",100),("type",140),("modified",160)]:
            self.tree.heading(k,text={"size":"大小","type":"类型","modified":"修改日期"}[k],
                anchor="w",command=lambda c=k:self._sort(c))
            self.tree.column(k,width=w,minwidth=60,anchor="w")
        self.tree.bind("<Double-Button-1>",self._od)
        self.tree.bind("<Button-1>",self._tc,add="+")
        self.tree.pack(side="left",fill="both",expand=True)
        vsb=ttk.Scrollbar(self.mn,orient="v",command=self.tree.yview)
        vsb.pack(side="right",fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        self.ft=tk.Frame(self.root,bg=t["bg"],height=24)
        self.ft.pack(fill="x");self.ft.pack_propagate(False)
        self.fl=tk.Label(self.ft,text="",bg=t["bg"],fg=t["ft"],font=("Consolas",9),anchor="w",padx=12)
        self.fl.pack(fill="x")

    def _build_bar(self):
        t=self._t
        self.bar=tk.Canvas(self.root,height=50,highlightthickness=0,bg=t["bb"])
        self.bar.pack(fill="x")
        self._bar_bg_id=self.bar.create_image(0,0,anchor="nw")
        self._bar_photo=None
        # 交通灯：直接画椭圆，无嵌入 widget，无边框
        for cx,col,cmd in[(20,"#ff5f57",self.root.destroy),(44,"#febc2e",self._min),(68,"#28c840",self._max)]:
            oid=self.bar.create_oval(cx-9,16,cx+9,34,fill=col,outline="")
            dc=self._dk(col)
            self.bar.tag_bind(oid,"<Enter>",lambda e,o=oid,d=dc:(self.bar.itemconfig(o,fill=d),self.bar.configure(cursor="hand2")))
            self.bar.tag_bind(oid,"<Leave>",lambda e,o=oid,c=col:(self.bar.itemconfig(o,fill=c),self.bar.configure(cursor="")))
            self.bar.tag_bind(oid,"<Button-1>",lambda e,f=cmd:f())
        # 文字按钮
        self._bar_btns={};self.pv=tk.StringVar()
        for bname,bx,btxt,bcmd in[("back",104,"◀",self._b),("fwd",132,"▶",self._f),
                                   ("pin",164,"📌",self._toggle_pin),("theme",196,TN[2],self._cycle)]:
            bg_id=self.bar.create_rectangle(bx-18,4,bx+18,46,fill="",outline="")
            txt_id=self.bar.create_text(bx,25,text=btxt,fill=t["bn"],font=("Segoe UI",11))
            hit_id=self.bar.create_rectangle(bx-18,4,bx+18,46,fill="",outline="")
            self.bar.tag_bind(hit_id,"<Enter>",lambda e,b=bg_id,tx=txt_id:(
                self.bar.itemconfig(b,fill=self._t["sa"]),self.bar.itemconfig(tx,fill=self._t["fg"]),self.bar.configure(cursor="hand2")))
            self.bar.tag_bind(hit_id,"<Leave>",lambda e,b=bg_id,tx=txt_id:(
                self.bar.itemconfig(b,fill=""),self.bar.itemconfig(tx,fill=self._t["bn"]),self.bar.configure(cursor="")))
            self.bar.tag_bind(hit_id,"<Button-1>",lambda e,c=bcmd:c())
            self._bar_btns[bname]=(bg_id,txt_id,hit_id)
        # 路径栏（右对齐，宽度跟随窗口）
        self.pe=tk.Entry(self.bar,textvariable=self.pv,bg=t["pb"],fg=t["pf"],
            font=("Segoe UI",10),bd=0,insertbackground=t["fg"],relief="flat",highlightthickness=0)
        self.pe.bind("<Return>",self._pn)
        self._pe_w=max(300,W-580)
        self._pe_id=self.bar.create_window(W-12-self._pe_w//2,25,anchor="center",window=self.pe,height=28,width=self._pe_w)
        self._bar_drag_id=self.bar.create_rectangle(220,0,W-self._pe_w-30,50,fill="",outline="",tags="bar_drag")
        self.bar.itemconfig(self._pe_id,state="hidden")  # 默认显示面包屑，编辑时才显示 Entry
        self.bar.bind("<Configure>",self._bar_on_configure)

    def _bar_on_configure(self,e):
        w=e.width
        self._pe_w=max(300,w-580)
        self.bar.itemconfig(self._pe_id,width=self._pe_w)
        self.bar.coords(self._pe_id,w-12-self._pe_w//2,25)
        self.bar.coords(self._bar_drag_id,220,0,max(221,w-self._pe_w-30),50)
        self._update_bc()

    def _cycle(self):
        self._apply((self.ti+1)%len(THEMES))

    # 260518 Red 交通灯悬停改为 macOS 风格：仅变暗 fill，不改 canvas bg，无黑边
    @staticmethod
    def _dk(c,f=0.82):
        r,g,b=int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"
    # 侧边栏全 Canvas 绘制，支持毛玻璃背景图透出
    def _sb(self):
        t=self._t;c=self.sd
        for item in c.find_all():
            if item!=getattr(self,"_sd_bg_id",None):c.delete(item)
        c.create_text(16,14,text="位置",anchor="w",fill=t["bn"],font=("Segoe UI",9,"bold"))
        y=36
        for lbl,pa in[("🏠 Home",os.path.expanduser("~")),("🖥 桌面",
            os.path.join(os.path.expanduser("~"),"Desktop")),("⬇ 下载",
            os.path.join(os.path.expanduser("~"),"Downloads")),("📄 文档",
            os.path.join(os.path.expanduser("~"),"Documents")),("🖼 图片",
            os.path.join(os.path.expanduser("~"),"Pictures")),("🎵 音乐",
            os.path.join(os.path.expanduser("~"),"Music")),("🎬 视频",
            os.path.join(os.path.expanduser("~"),"Videos"))]:
            y=self._sb_row(c,y,30,lbl,pa,t,False)
        top3=[p for p in sorted(self._freq,key=self._freq.get,reverse=True)[:6]if os.path.isdir(p)][:3]
        if top3:
            y+=6
            c.create_text(16,y+7,text="常用",anchor="w",fill=t["bn"],font=("Segoe UI",8,"bold"))
            y+=20
            for p in top3:
                nm=os.path.basename(p) or p
                y=self._sb_row(c,y,28,"📁 "+nm,p,t,False)
            y+=4
        for r,l in drives():
            name=(f"{l} ({r[0].rstrip(chr(92))})"if l else r[0].rstrip(chr(92)))
            y=self._sb_row(c,y,30,name,r,t,True)

    def _sb_row(self,c,y,h,label,path,t,icon):
        bg=c.create_rectangle(0,y,9999,y+h,fill="",outline="",tags="fw")
        if icon:
            ix,iy=16,y+h//2-5
            c.create_rectangle(ix,iy+2,ix+18,iy+12,fill="#8c8c8c",outline="#5a5a5a")
            c.create_rectangle(ix+1,iy+3,ix+17,iy+6,fill="#c0c0c0",outline="")
            c.create_oval(ix+13,iy+8,ix+17,iy+12,fill="#29b6f6",outline="")
            tx=42
        else:
            tx=16
        c.create_text(tx,y+h//2,text=label,anchor="w",fill=t["sf"],font=("Segoe UI",10))
        hit=c.create_rectangle(0,y,9999,y+h,fill="",outline="",tags="fw")
        c.tag_bind(hit,"<Enter>",lambda e,b=bg:(c.itemconfig(b,fill=t["sa"]),c.configure(cursor="hand2")))
        c.tag_bind(hit,"<Leave>",lambda e,b=bg:(c.itemconfig(b,fill=""),c.configure(cursor="")))
        c.tag_bind(hit,"<Button-1>",lambda e,p=path:self._nav(p))
        return y+h

    def _sd_on_configure(self,e):
        w=e.width
        for item in self.sd.find_withtag("fw"):
            coords=self.sd.coords(item)
            if len(coords)==4:self.sd.coords(item,0,coords[1],w,coords[3])

    def _refresh_glass(self):
        """一次截取整个窗口背后区域，分别裁剪顶部栏和侧边栏，无需隐藏窗口"""
        if not hasattr(self,"sd") or not self.sd.winfo_exists():return
        self.root.update_idletasks()
        rx=self.root.winfo_x();ry=self.root.winfo_y()
        rw=self.root.winfo_width();rh=self.root.winfo_height()
        if rw<=2 or rh<=2:return
        try:img=ImageGrab.grab(bbox=(rx,ry,rx+rw,ry+rh))
        except:return
        bh=max(1,self.bar.winfo_height())
        sw=max(1,self.sd.winfo_width())
        # 裁剪顶部栏和侧边栏区域
        self._bar_blur_raw=img.crop((0,0,rw,bh)).filter(ImageFilter.GaussianBlur(radius=20))
        self._sd_blur_raw=img.crop((0,bh,sw,rh)).filter(ImageFilter.GaussianBlur(radius=20))
        self._apply_bar_glass_tint()
        self._apply_glass_tint()

    def _apply_glass_tint(self):
        if not self._sd_blur_raw:return
        t=self._t
        r,g,b=int(t["sb"][1:3],16),int(t["sb"][3:5],16),int(t["sb"][5:7],16)
        overlay=Image.new("RGB",self._sd_blur_raw.size,(r,g,b))
        self._sd_photo=ImageTk.PhotoImage(Image.blend(self._sd_blur_raw,overlay,0.5))
        self.sd.itemconfig(self._sd_bg_id,image=self._sd_photo)

    def _apply_bar_glass_tint(self):
        if not hasattr(self,"_bar_blur_raw") or not self._bar_blur_raw:return
        t=self._t
        r,g,b=int(t["bb"][1:3],16),int(t["bb"][3:5],16),int(t["bb"][5:7],16)
        overlay=Image.new("RGB",self._bar_blur_raw.size,(r,g,b))
        self._bar_photo=ImageTk.PhotoImage(Image.blend(self._bar_blur_raw,overlay,0.5))
        self.bar.itemconfig(self._bar_bg_id,image=self._bar_photo)

    # 260518 Red 重命名 _sd 为 _sash_d，避免与侧边栏 Frame self.sd 命名冲突
    def _sash_start(self,e):
        self._sash_d={"x":e.x_root,"w":self.sd.winfo_width()}
        self.root.configure(cursor="sb_h_double_arrow")
    def _sash_drag(self,e):
        if"x"in self._sash_d:
            nw=max(SW_MIN,min(SW_MAX,self._sash_d["w"]+e.x_root-self._sash_d["x"]))
            self.sd.configure(width=nw)

    def _nav(self,p):
        p=os.path.abspath(p)
        if not os.path.exists(p):return
        if self.hp<len(self.hist)-1:self.hist=self.hist[:self.hp+1]
        self.hist.append(p);self.hp+=1;self.cp=p
        self._freq[p]=self._freq.get(p,0)+1
        try:
            with open(self._freq_path,"w",encoding="utf-8")as f:json.dump(self._freq,f)
        except:pass
        self.root.after_idle(self._sb)
        self._tabs[self._active_tab].update({"path":p,"hist":self.hist[:],"hp":self.hp})
        self.pv.set(p);self._ub();self._ls(p);self._update_bc();self._draw_tabs()

    def _ls(self,p):
        for i in self.tree.get_children():self.tree.delete(i)
        rows=[];self._ip={}
        try:
            with os.scandir(p) as it:
                for e in it:
                    if not self._sh and e.name.startswith("."):continue
                    try:
                        s=e.stat();d=e.is_dir()
                        rows.append({"n":e.name,"f":e.path,"d":d,"s":s.st_size if not d else 0,"m":s.st_mtime})
                    except:pass
        except:self.fl.configure(text="无法读取");return
        self._sr(rows)
        for i,r in enumerate(rows):
            iid=self.tree.insert("","end",text=f"  {fi(r['n'],r['d'])}  {r['n']}",
                values=(""if r["d"]else fs(r["s"]),"文件夹"if r["d"]else ft(r["n"]),fd(r["m"])))
            self._ip[iid]=r["f"]
        fc=sum(1 for r in rows if r["d"]);fl=len(rows)-fc
        self.fl.configure(text=f"{len(rows)} 项 | {fc} 文件夹 | {fl} 文件")

    def _sr(self,rows):
        km={"name":lambda r:(not r["d"],r["n"].lower()),"size":lambda r:(not r["d"],r["s"]),
            "type":lambda r:(not r["d"],ft(r["n"])),"modified":lambda r:(not r["d"],r["m"])}
        rows.sort(key=km.get(self.sc,km["name"]),reverse=not self.sa)
    def _sort(self,c):
        if self.sc==c:self.sa=not self.sa;self._ls(self.cp)
        else:self.sc=c;self.sa=True;self._ls(self.cp)

    # ── 鼠标事件 ──
    def _rme(self,rx,ry):
        x=self.root.winfo_x();y=self.root.winfo_y()
        w=self.root.winfo_width();h=self.root.winfo_height()
        rx-=x;ry-=y;m=RM
        L=rx<m;R=rx>w-m;T=ry<m;B=ry>h-m
        if T&L:return"nw"
        if T&R:return"ne"
        if B&L:return"sw"
        if B&R:return"se"
        if L:return"w"
        if R:return"e"
        if T:return"n"
        if B:return"s"
        return None

    def _click(self,e):
        rm=self._rme(e.x_root,e.y_root)
        if rm:
            self._rm=rm;self._rd={"x":e.x_root,"y":e.y_root,
                "wx":self.root.winfo_x(),"wy":self.root.winfo_y(),
                "ww":self.root.winfo_width(),"wh":self.root.winfo_height()}
            return
        if e.widget==self.bar:
            items=self.bar.find_overlapping(e.x,e.y,e.x+1,e.y+1)
            if items and"bar_drag"in self.bar.gettags(items[-1]):
                self._wd={"x":e.x_root,"y":e.y_root,"wx":self.root.winfo_x(),"wy":self.root.winfo_y()}

    def _drag(self,e):
        if self._rm and self._rd:
            d=self._rd;dx=e.x_root-d["x"];dy=e.y_root-d["y"]
            x,y,w,h=d["wx"],d["wy"],d["ww"],d["wh"];m=self._rm
            if"e"in m:w=max(MIN_W,d["ww"]+dx)
            if"s"in m:h=max(MIN_H,d["wh"]+dy)
            if"w"in m:
                nw=max(MIN_W,d["ww"]-dx)
                if nw!=d["ww"]:x=d["wx"]+(d["ww"]-nw);w=nw
            if"n"in m:
                nh=max(MIN_H,d["wh"]-dy)
                if nh!=d["wh"]:y=d["wy"]+(d["wh"]-nh);h=nh
            self.root.geometry(f"{w}x{h}+{x}+{y}");self.root.update_idletasks();return
        if self._wd and self._hwnd:
            nx=self._wd["wx"]+e.x_root-self._wd["x"]
            ny=self._wd["wy"]+e.y_root-self._wd["y"]
            ctypes.windll.user32.SetWindowPos(self._hwnd,None,nx,ny,0,0,0x0001|0x0004|0x0010)

    def _rel(self,e):
        self._rd={};self._wd={};self._sash_d={};self._rm=None;self.root.configure(cursor="")
        self.root.after(200,self._refresh_glass)
    def _move(self,e):
        rm=self._rme(e.x_root,e.y_root)
        c={"n":"sb_v_double_arrow","s":"sb_v_double_arrow","w":"sb_h_double_arrow","e":"sb_h_double_arrow",
           "nw":"size_nw_se","ne":"size_ne_sw","sw":"size_ne_sw","se":"size_nw_se"}.get(rm,"")
        self.root.configure(cursor=c)

    def _sel_path(self):
        i=self.tree.focus();return self._ip.get(i,"")if i else""
    def _od(self,e):
        p=self._sel_path()
        if p:
            if os.path.isdir(p):self._nav(p)
            else:openf(p)
    def _tc(self,e):
        if not self.tree.identify_row(e.y):self.tree.selection_remove(self.tree.selection())

    def _b(self):
        if self.hp>0:
            self.hp-=1;self.cp=self.hist[self.hp];self.pv.set(self.cp);self._ls(self.cp);self._ub()
            self._tabs[self._active_tab].update({"path":self.cp,"hist":self.hist[:],"hp":self.hp})
            self._update_bc();self._draw_tabs()
    def _f(self):
        if self.hp<len(self.hist)-1:
            self.hp+=1;self.cp=self.hist[self.hp];self.pv.set(self.cp);self._ls(self.cp);self._ub()
            self._tabs[self._active_tab].update({"path":self.cp,"hist":self.hist[:],"hp":self.hp})
            self._update_bc();self._draw_tabs()
    def _ub(self):
        t=self._t
        self.bar.itemconfig(self._bar_btns["back"][1],fill=t["bn"]if self.hp>0 else"#888888")
        self.bar.itemconfig(self._bar_btns["fwd"][1],fill=t["bn"]if self.hp<len(self.hist)-1 else"#888888")
    def _pn(self,e):
        p=self.pv.get().strip()
        if os.path.exists(p):self._nav(p)
        self._bc_edit_end()
    def _min(self):
        self.root.iconify()
    def _on_map(self,e):
        if e.widget is not self.root:return
        self._iconified=False
        self.root.after(200,self._refresh_glass)
    def _on_unmap(self,e):
        if e.widget is not self.root:return
        self._iconified=True
    def _max(self):
        if hasattr(self,"_pre_max"):
            self.root.geometry(self._pre_max);del self._pre_max
        else:
            self._pre_max=f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_x()}+{self.root.winfo_y()}"
            r=ctypes.wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030,0,ctypes.byref(r),0)
            self.root.geometry(f"{r.right-r.left}x{r.bottom-r.top}+{r.left}+{r.top}")
        self.root.after(200,self._refresh_glass)

    def _cm_show(self,e):
        i=self.tree.identify_row(e.y)
        if i:self.tree.focus(i);self.tree.selection_set(i)
        self.cmenu.tk_popup(e.x_root,e.y_root)
    def _cm_open(self):
        p=self._sel_path()
        if p:
            if os.path.isdir(p):self._nav(p)
            else:openf(p)
    def _cm_copy(self):
        p=self._sel_path()
        if p:self.root.clipboard_clear();self.root.clipboard_append(p);self._clip_cut=False
    def _cm_cut(self):
        p=self._sel_path()
        if p:self.root.clipboard_clear();self.root.clipboard_append(p);self._clip_cut=True
    def _cm_paste(self):
        try:
            src=self.root.clipboard_get()
            if not os.path.exists(src):return
            dst=os.path.join(self.cp,os.path.basename(src))
            if os.path.exists(dst):return
            if self._clip_cut:os.rename(src,dst)
            else:
                shutil.copytree(src,dst,dirs_exist_ok=True)if os.path.isdir(src)else shutil.copy2(src,dst)
            self._ls(self.cp)
        except:pass
    def _cm_rename(self):
        p=self._sel_path()
        if not p:return
        import tkinter.simpledialog as sd
        n=sd.askstring("重命名","新名称:",initialvalue=os.path.basename(p),parent=self.root)
        if n and n!=os.path.basename(p):
            try:os.rename(p,os.path.join(os.path.dirname(p),n))
            except:pass
            self._ls(self.cp)
    def _cm_delete(self):
        p=self._sel_path()
        if not p:return
        import tkinter.messagebox as mb
        if mb.askyesno("确认删除",f"确定删除 {os.path.basename(p)}？",parent=self.root):
            try:
                if os.path.isfile(p):os.remove(p)
                else:shutil.rmtree(p)
                self._ls(self.cp)
            except:pass

    def _cm_move(self):
        p=self._sel_path()
        if not p:return
        # 260518 Red 修复 filedialog 未导入导致"移动到..."崩溃
        from tkinter import filedialog
        d=filedialog.askdirectory(title="移动到...",parent=self.root)
        if d:
            try:
                dst=os.path.join(d,os.path.basename(p))
                if not os.path.exists(dst):
                    shutil.move(p,dst)
                self._ls(self.cp)
            except:pass
    def _cm_newfolder(self):
        import tkinter.simpledialog as dlg
        n=dlg.askstring("新建文件夹","文件夹名称:",initialvalue="新建文件夹",parent=self.root)
        if n:
            try:os.makedirs(os.path.join(self.cp,n),exist_ok=True)
            except:pass
            self._ls(self.cp)

    def _cm_openwith(self):
        p=self._sel_path()
        if not p or os.path.isdir(p):return
        try:ctypes.windll.shell32.ShellExecuteW(self.root.winfo_id(),"openas",p,None,None,1)
        except:pass

    def _cm_properties(self):
        p=self._sel_path()
        if not p:return
        t=self._t
        try:s=os.stat(p)
        except:return
        is_dir=os.path.isdir(p)
        name=os.path.basename(p)
        if is_dir:
            try:
                total=sum(os.path.getsize(os.path.join(dp,f))
                    for dp,_,files in os.walk(p) for f in files)
                count=sum(1 for _ in os.scandir(p))
                size_str=f"{fs(total)}（{count} 项）"
            except:size_str="—"
            type_str="文件夹";icon_str="📁"
        else:
            size_str=fs(s.st_size);type_str=ft(name);icon_str=fi(name,False)
        win=tk.Toplevel(self.root)
        win.title("属性");win.configure(bg=t["bg"])
        win.resizable(False,False);win.transient(self.root);win.grab_set()
        tk.Label(win,text=f"{icon_str}  {name}",bg=t["bg"],fg=t["fg"],
            font=("Segoe UI",13,"bold"),anchor="w",padx=20,pady=14).pack(fill="x")
        tk.Frame(win,bg=t["ft"],height=1).pack(fill="x",padx=20)
        for lbl,val in[("类型",type_str),("位置",os.path.dirname(p)),
                       ("大小",size_str),("创建",fd(s.st_ctime)),("修改",fd(s.st_mtime))]:
            row=tk.Frame(win,bg=t["bg"]);row.pack(fill="x",padx=20,pady=3)
            tk.Label(row,text=lbl+"：",bg=t["bg"],fg=t["ft"],font=("Segoe UI",9),
                width=5,anchor="e").pack(side="left")
            tk.Label(row,text=val,bg=t["bg"],fg=t["fg"],font=("Segoe UI",9),
                anchor="w",wraplength=300,justify="left").pack(side="left",padx=(6,0))
        tk.Frame(win,bg=t["ft"],height=1).pack(fill="x",padx=20,pady=(12,0))
        tk.Button(win,text="确定",bg=t["sa"],fg=t["fg"],font=("Segoe UI",10),
            relief="flat",padx=24,pady=6,cursor="hand2",
            command=win.destroy).pack(pady=12)
        win.update_idletasks()
        pw=self.root.winfo_x()+(self.root.winfo_width()-win.winfo_width())//2
        ph=self.root.winfo_y()+(self.root.winfo_height()-win.winfo_height())//2
        win.geometry(f"+{pw}+{ph}")

    def _cm_hidden(self):
        self._sh=not self._sh
        self._ls(self.cp)
        # 260518 Red 修复隐藏文件菜单标签逻辑反转（原 not self._sh 条件错误）
        self.cmenu.entryconfig(self._hidden_idx,label="隐藏隐藏文件"if self._sh else"显示隐藏文件")

    def _toggle_pin(self):
        t=self.root.attributes("-topmost")
        self.root.attributes("-topmost",not t)
        self.bar.itemconfig(self._bar_btns["pin"][1],
            fill="#007aff"if not t else self._t["bn"],text="📌"if not t else"📍")

    def _selected(self):
        i=self.tree.focus();p=self._ip.get(i,"")
        return p if p and os.path.exists(p)else None

    def on_key(self,e):
        if e.widget is self.pe:return  # 路径编辑中，不拦截
        if e.keysym=="F5":self._ls(self.cp)
        elif e.keysym=="BackSpace":
            p=os.path.dirname(self.cp)
            if p!=self.cp:self._nav(p)
        elif e.keysym=="Return":
            p=self._selected()
            if p:
                if os.path.isdir(p):self._nav(p)
                else:openf(p)
        elif e.keysym=="Delete":
            p=self._selected()
            if p:self._cm_delete()
        elif e.keysym=="F2":self._cm_rename()
        elif e.keysym=="space":self._quick_look()
        elif e.keysym=="Escape":
            if hasattr(self,"_ql_win") and self._ql_win:self._ql_close()
            else:self.root.destroy()
        elif e.keysym=="c"and e.state&4:self._cm_copy()
        elif e.keysym=="x"and e.state&4:self._cm_cut()
        elif e.keysym=="v"and e.state&4:self._cm_paste()
        elif e.keysym=="N"and e.state&4:self._cm_newfolder()
        elif e.keysym=="t"and e.state&4:self._tab_new()
        elif e.keysym=="w"and e.state&4:self._tab_close(self._active_tab)
        elif e.keysym=="Tab"and e.state&4:
            n=len(self._tabs)
            if n>1:self._tab_switch((self._active_tab+(-1 if e.state&1 else 1))%n)
    # ── 标签页 ──
    def _build_tabs_bar(self):
        t=self._t
        self.tabs_bar=tk.Canvas(self.root,height=30,highlightthickness=0,bg=t["bg"])
        self.tabs_bar.pack(fill="x")
        self.tabs_bar.bind("<Configure>",lambda e:self._draw_tabs())

    def _draw_tabs(self):
        if not hasattr(self,"tabs_bar"):return
        c=self.tabs_bar;c.delete("all")
        t=self._t;cw=max(1,c.winfo_width())
        n=len(self._tabs);tab_w=max(80,min(200,(cw-34)//n))
        for i,tab in enumerate(self._tabs):
            x=i*tab_w;act=(i==self._active_tab)
            bg=t["sl"] if act else t["bg"]
            c.create_rectangle(x,0,x+tab_w,30,fill=bg,outline="")
            if act:c.create_line(x,0,x+tab_w,0,fill=t["sel"],width=2)
            else:c.create_line(x,29,x+tab_w,29,fill=t["ft"],width=1)
            name=os.path.basename(tab["path"])or tab["path"]
            if len(name)>22:name=name[:20]+"…"
            tx=x+tab_w//2-(9 if n>1 else 0)
            c.create_text(tx,15,text=name,anchor="center",
                fill=t["fg"] if act else t["bn"],font=("Segoe UI",9))
            hit=c.create_rectangle(x,0,x+tab_w-(20 if n>1 else 0),30,fill="",outline="")
            c.tag_bind(hit,"<Button-1>",lambda e,ii=i:self._tab_switch(ii))
            c.tag_bind(hit,"<Enter>",lambda e:c.configure(cursor="hand2"))
            c.tag_bind(hit,"<Leave>",lambda e:c.configure(cursor=""))
            if n>1:
                xb=c.create_text(x+tab_w-11,15,text="×",anchor="center",
                    fill=t["ft"],font=("Segoe UI",11))
                bh=c.create_rectangle(x+tab_w-22,4,x+tab_w-2,26,fill="",outline="")
                c.tag_bind(xb,"<Enter>",lambda e,xi=xb:(c.itemconfig(xi,fill=t["fg"]),c.configure(cursor="hand2")))
                c.tag_bind(xb,"<Leave>",lambda e,xi=xb:(c.itemconfig(xi,fill=t["ft"]),c.configure(cursor="")))
                c.tag_bind(bh,"<Button-1>",lambda e,ii=i:self._tab_close(ii))
        px=n*tab_w
        pl=c.create_text(px+16,15,text="+",anchor="center",fill=t["bn"],font=("Segoe UI",13))
        ph=c.create_rectangle(px+2,3,px+30,27,fill="",outline="")
        c.tag_bind(pl,"<Enter>",lambda e:(c.itemconfig(pl,fill=t["fg"]),c.configure(cursor="hand2")))
        c.tag_bind(pl,"<Leave>",lambda e:(c.itemconfig(pl,fill=t["bn"]),c.configure(cursor="")))
        c.tag_bind(ph,"<Button-1>",lambda e:self._tab_new())

    def _tab_new(self,path=None):
        self._tabs[self._active_tab].update({"path":self.cp,"hist":self.hist[:],"hp":self.hp})
        p=path or self.cp
        self._tabs.append({"path":p,"hist":[p],"hp":0})
        self._active_tab=len(self._tabs)-1
        self.cp=p;self.hist=[p];self.hp=0
        self.pv.set(p);self._ub();self._ls(p);self._update_bc();self._draw_tabs()

    def _tab_close(self,idx):
        if len(self._tabs)<=1:return
        self._tabs.pop(idx)
        new=min(idx,len(self._tabs)-1);self._active_tab=new
        tab=self._tabs[new]
        self.cp=tab["path"];self.hist=tab["hist"][:];self.hp=tab["hp"]
        self.pv.set(self.cp);self._ub();self._ls(self.cp);self._update_bc();self._draw_tabs()

    def _tab_switch(self,idx):
        if idx==self._active_tab:return
        self._tabs[self._active_tab].update({"path":self.cp,"hist":self.hist[:],"hp":self.hp})
        self._active_tab=idx;tab=self._tabs[idx]
        self.cp=tab["path"];self.hist=tab["hist"][:];self.hp=tab["hp"]
        self.pv.set(self.cp);self._ub();self._ls(self.cp);self._update_bc();self._draw_tabs()

    # ── 面包屑路径栏 ──
    def _update_bc(self):
        if not hasattr(self,"bar"):return
        for item in self.bar.find_withtag("bc"):self.bar.delete(item)
        if self._bc_edit:return
        cw=max(1,self.bar.winfo_width())
        if cw<=2:return
        t=self._t
        # 拆分路径为各段
        parts=[];cur=os.path.normpath(self.cp)
        while True:
            head,tail=os.path.split(cur)
            if tail:parts.insert(0,(tail,cur));cur=head
            else:
                if cur:parts.insert(0,(cur,cur))
                break
        # 按可用宽度从左截断
        left=cw-12-self._pe_w+8;avail=self._pe_w-20
        while len(parts)>1:
            total=sum(len(n)*7+14 for n,_ in parts)
            if total<=avail:break
            parts=[("…",None)]+parts[2:]
        # 绘制
        x=left;y=25
        zone=self.bar.create_rectangle(left,8,cw-16,42,fill="",outline="",tags="bc")
        self.bar.tag_bind(zone,"<Double-Button-1>",self._bc_edit_start)
        for i,(name,path) in enumerate(parts):
            is_last=(i==len(parts)-1)
            col=t["fg"] if is_last else t["bn"]
            txt=self.bar.create_text(x,y,text=name,anchor="w",fill=col,
                font=("Segoe UI",10),tags="bc")
            bb=self.bar.bbox(txt)
            if bb:
                if path:
                    hit=self.bar.create_rectangle(bb[0],8,bb[2]+2,42,fill="",outline="",tags="bc")
                    self.bar.tag_bind(hit,"<Button-1>",lambda e,pp=path:self._nav(pp))
                    self.bar.tag_bind(hit,"<Enter>",lambda e,ti=txt:(
                        self.bar.itemconfig(ti,fill=self._t["fg"]),self.bar.configure(cursor="hand2")))
                    self.bar.tag_bind(hit,"<Leave>",lambda e,ti=txt,c=col:(
                        self.bar.itemconfig(ti,fill=c),self.bar.configure(cursor="")))
                x=bb[2]+3
            else:x+=len(name)*7+3
            if not is_last:
                s=self.bar.create_text(x,y,text="›",anchor="w",fill=t["ft"],
                    font=("Segoe UI",10),tags="bc")
                bb2=self.bar.bbox(s)
                x=(bb2[2] if bb2 else x+12)+3

    def _bc_edit_start(self,e=None):
        self._bc_edit=True
        for item in self.bar.find_withtag("bc"):self.bar.delete(item)
        self.bar.itemconfig(self._pe_id,state="normal")
        self.pe.focus_set();self.pe.select_range(0,"end")
        self.pe.bind("<FocusOut>",self._bc_edit_end)

    def _bc_edit_end(self,e=None):
        self._bc_edit=False
        self.bar.itemconfig(self._pe_id,state="hidden")
        self.pe.unbind("<FocusOut>")
        self._update_bc()

    # ── Quick Look 空格预览 ──
    def _quick_look(self):
        p=self._sel_path()
        if not p:return
        if hasattr(self,"_ql_win") and self._ql_win:
            try:self._ql_win.destroy()
            except:pass
            self._ql_win=None;return
        t=self._t
        ext=os.path.splitext(p)[1].lower()
        img_exts={".jpg",".jpeg",".png",".gif",".bmp",".webp",".ico",".tiff",".tif"}
        txt_exts={".txt",".md",".py",".js",".ts",".css",".html",".json",".xml",
            ".csv",".log",".ini",".cfg",".yaml",".yml",".toml",".sh",".bat",
            ".c",".cpp",".h",".java",".rs",".go",".rb",".php",".sql",".vue",".tsx"}
        win=tk.Toplevel(self.root)
        win.overrideredirect(True);win.configure(bg=t["sh"])
        win.attributes("-topmost",True);self._ql_win=win
        inner=tk.Frame(win,bg=t["bg"]);inner.pack(fill="both",expand=True,padx=2,pady=2)
        # 标题栏
        hdr=tk.Frame(inner,bg=t["bb"],height=34);hdr.pack(fill="x");hdr.pack_propagate(False)
        name=os.path.basename(p)
        tk.Label(hdr,text=name,bg=t["bb"],fg=t["fg"],font=("Segoe UI",10,"bold")).pack(expand=True)
        shown=False
        # 图片预览
        if ext in img_exts:
            try:
                img=Image.open(p);img.thumbnail((760,460),Image.LANCZOS)
                photo=ImageTk.PhotoImage(img)
                lbl=tk.Label(inner,image=photo,bg=t["bg"]);lbl.image=photo;lbl.pack(padx=16,pady=12)
                shown=True
            except:pass
        # 文本/代码预览（含文件夹列表）
        if not shown:
            if os.path.isdir(p):
                try:
                    items=sorted(os.scandir(p),key=lambda e:(not e.is_dir(),e.name.lower()))[:40]
                    content="\n".join(("📁  " if e.is_dir() else "📄  ")+e.name for e in items)
                    if not content:content="（空文件夹）"
                except:content="无法读取"
                shown=True
            elif ext in txt_exts:
                try:
                    with open(p,"r",encoding="utf-8",errors="replace") as f:content=f.read(8000)
                    shown=True
                except:pass
            if shown:
                frm=tk.Frame(inner,bg=t["sl"]);frm.pack(padx=12,pady=12,fill="both",expand=True)
                txt=tk.Text(frm,bg=t["sl"],fg=t["fg"],font=("Consolas",9),relief="flat",
                    bd=0,width=80,height=22,wrap="none",padx=8,pady=8)
                vsb=ttk.Scrollbar(frm,orient="v",command=txt.yview)
                txt.configure(yscrollcommand=vsb.set)
                vsb.pack(side="right",fill="y");txt.pack(fill="both",expand=True)
                txt.insert("1.0",content);txt.configure(state="disabled")
        # 通用文件信息兜底
        if not shown:
            try:s=os.stat(p);info=f"\n{fi(name,False)}\n\n{name}\n\n大小：{fs(s.st_size)}\n修改：{fd(s.st_mtime)}"
            except:info=f"\n{name}"
            tk.Label(inner,text=info,bg=t["bg"],fg=t["fg"],font=("Segoe UI",12)).pack(pady=30)
        tk.Label(inner,text="空格 / Esc 关闭",bg=t["bg"],fg=t["ft"],font=("Segoe UI",8)).pack(pady=(0,8))
        win.update_idletasks()
        pw=self.root.winfo_x()+(self.root.winfo_width()-win.winfo_width())//2
        ph=self.root.winfo_y()+(self.root.winfo_height()-win.winfo_height())//2
        win.geometry(f"+{pw}+{ph}");win.focus_set()

    def _ql_close(self):
        if hasattr(self,"_ql_win") and self._ql_win:
            try:self._ql_win.destroy()
            except:pass
            self._ql_win=None

    def run(self):self.root.mainloop()

if __name__=="__main__":
    RFile().run()
