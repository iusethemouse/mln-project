import tkinter as tk
from tkinter import ttk
import uunet.multinet as ml
import json
import numpy
import matplotlib
import matplotlib.pyplot as plt 
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pathlib

import parser

MLNinFname = ""
STEinFname = ""
OUTFname = "out.py" 


def df(d):
    return pandas.DataFrame.from_dict(d)


def file_opener():
    filename = tk.filedialog.askopenfilename(initialdir=pathlib.Path(__file__).parent.resolve())
    filename = filename.split('/')[-1]
    if '.txt' in filename:
        global MLNinFname
        MLNinFname = filename
        lbl_MLNinput.config(text=f'Selected network file: {filename}')
    elif ('.mln' or '.ste') in filename:
        global STEinFname
        STEinFname = filename
        lbl_STEinput.config(text=f'Selected language file: {filename}')


def viz_mln():
    global MLNinFname
#     MLNinFname = ent_MLNinput.get()
    net = ml.read(MLNinFname)
    l1 = ml.layout_multiforce(net, w_inter = [0] , gravity = [1])
    ml.plot( net , layout = l1 , vertex_labels_bbox = {"boxstyle":'round4' , "fc":'white'})
    

def run_mln():
    OUTFname = "out_new.py"
    #### THIS WAY it's not right, once we change the stuff he still keeps the old stuff so when doing import again it keeps executing using the old object
    from out_new import Mln_dynamics
    from out_new import run_sim
    model = Mln_dynamics()
    run_sim(model)


def export_to_kappa():
    global MLNinFname
    global STEinFname
    out_filename = 'out_kappa.txt'

    parser.parse_to_kappa(MLNinFname, STEinFname, out_filename)

    lbl_kappa_status.config(text=f'Successfully exported to Kappa.')



#### Building and managing the GUI
window = tk.Tk()
window.title('Prototype')

frm_MLNinput = tk.Frame(master=window , borderwidth=1)
frm_MLNinput.grid(row=0,column=0, pady=5)
frm_STEinput = tk.Frame(master=window , borderwidth=1)
frm_STEinput.grid(row=1,column=0, pady=5)
frm_OUToptions = tk.Frame(master=window, borderwidth=1)
frm_OUToptions.grid(row=2,column=0, pady=5)

frm_execute = tk.Frame(master=window , borderwidth = 1 )
frm_execute.grid(row=3, column=0)

btn_select_net = tk.Button(master = frm_MLNinput, text="Select MLN file", command=lambda: file_opener())
btn_select_net.pack()
lbl_MLNinput = tk.Label(master=frm_MLNinput , text="No network file selected.")
lbl_MLNinput.pack()
# ent_MLNinput = tk.Entry(master= frm_MLNinput)
# ent_MLNinput.pack()
separator_mln = ttk.Separator(frm_MLNinput, orient='horizontal')
separator_mln.pack(fill=tk.X)

btn_select_lang = tk.Button(master = frm_STEinput, text="Select language file", command=lambda: file_opener())
btn_select_lang.pack()
lbl_STEinput = tk.Label(master=frm_STEinput , text="No language file selected.")
lbl_STEinput.pack()
# ent_STEinput = tk.Entry(master=frm_STEinput)
# ent_STEinput.pack()
separator_lang = ttk.Separator(frm_STEinput, orient='horizontal')
separator_lang.pack(fill=tk.X)

# lbl_OUToptions = tk.Label(master=frm_OUToptions , text = "Enter name for the output file:")
# lbl_OUToptions.pack()
# ent_OUToptions = tk.Entry(master=frm_OUToptions)
# ent_OUToptions.pack()

# btn_execute = tk.Button(master = frm_execute, text="Export to Gillespie", command=lambda: compile_click(MLNinFname, STEinFname))
# btn_execute.pack()
# lbl_execute = tk.Label(master = frm_execute, text="")
# lbl_execute.pack()
# separator_compile = ttk.Separator(frm_execute, orient='horizontal')
# separator_compile.pack(fill=tk.X)
    
frm_MLNviz = tk.Frame(master=window ,  borderwidth=1)
frm_MLNviz.grid(row=3 , column=0)

btn_viz = tk.Button(master=frm_MLNviz, text="Visualise MLN", command = viz_mln)
btn_viz.pack()


frm_gillespie = tk.Frame(master=window ,  borderwidth=1)
frm_gillespie.grid(row=5 , column=0)
frm_gillespie_lbl = tk.Frame(master=window ,  borderwidth=1)
frm_gillespie_lbl.grid(row=6 , column=0)

btn_execute = tk.Button(master = frm_gillespie, text="Export to Gillespie", command=lambda: compile_click(MLNinFname, STEinFname))
btn_execute.pack(side=tk.LEFT, pady=5, padx=5)
lbl_execute = tk.Label(master = frm_gillespie_lbl, text="")
lbl_execute.pack(side=tk.LEFT, pady=5, padx=5)

btn_gillespie_run = tk.Button(master=frm_gillespie, text="Simulate using Gillespie", command = run_mln)
btn_gillespie_run.pack(side=tk.RIGHT, pady=5, padx=5)


frm_kappa = tk.Frame(master=window ,  borderwidth=1)
frm_kappa.grid(row=7 , column=0)
frm_kappa_lbl = tk.Frame(master=window ,  borderwidth=1)
frm_kappa_lbl.grid(row=8 , column=0)

btn_export_to_kappa = tk.Button(master=frm_kappa, text="Export to Kappa", command = export_to_kappa)
btn_export_to_kappa.pack(side=tk.LEFT, pady=5, padx=5)
lbl_kappa_status = tk.Label(master=frm_kappa_lbl , text="")
lbl_kappa_status.pack(side=tk.LEFT, pady=5, padx=5)

btn_kappa_run = tk.Button(master=frm_kappa, text="Simulate using Kappa")
btn_kappa_run.pack(side=tk.RIGHT, pady=5, padx=5)

###FOR FIGURES IN THE GUI
#fig_mln = Figure(figsize=(5,5) , dpi=100)
#fig_test = fig_mln.add_subplot(111)
#fig_test.plot(net , layout = l1 , vertex_labels_bbox = {"boxstyle":'round4' , "fc":'white'})
#canvas = FigureCanvasTkAgg(fig_mln,master=frm_MLNviz)
#canvas.draw()
#canvas.get_tk_widget().pack(side=tk.LEFT , fill=tk.BOTH , expand = True )

def viz_mln():
    global MLNinFname
#     MLNinFname = ent_MLNinput.get()
    net = ml.read(MLNinFname)
    l1 = ml.layout_multiforce(net, w_inter = [0] , gravity = [1])
    ml.plot( net , layout = l1 , vertex_labels_bbox = {"boxstyle":'round4' , "fc":'white'})
    

def run_mln():
    OUTFname = "out.py"
    #### THIS WAY it's not right, once we change the stuff he still keeps the old stuff so when doing import again it keeps executing using the old object
    from out import Mln_dynamics
    from out import run_sim
    model = Mln_dynamics()
    run_sim(model)

#### FIGURES




##### ADD NAVIGATION TOOLBAR, CURRENTLY NOT WORKING
#toolbar = NavigationToolbar2Tk(canvas,window )
#toolbar.update()
#canvas._tkcanvas.pack(side=tk.LEFT , fill=tk.BOTH , expand = True)

#### EVENTS AND STUFF STARTS FROM HERE



# def compile_click(event):
def compile_click(MLNinFname, STEinFname):
    OUTFname = "out_new.py"
    
    # parse the .txt network definition
    # mln_data = parser.parse_mln(MLNinFname)
    
    # parse the .ste language file and generate a Gillespy2 file out.py
    parser.parse_to_gillespy(MLNinFname, STEinFname, OUTFname)
    lbl_execute.config(text='Successfully exported to Gillespie.')
#     lbl_execute["text"] = "Generated out.py!"
    
    
    
### BIND EVENTS    

##### Button-1 refers to the left click of the mouse    
# btn_execute.bind("<Button-1>", compile_click)

### STARTING THE EVENT LOOP (needed to start and keep the window running)
window.mainloop()

#### Destryoing windows
#### window.destroy() 

