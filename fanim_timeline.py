#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Copyright (C) 2016, Douglas Knowman
  douglasknowman@gmail.com

  Distributed under the terms of GNU GPL v3 (or lesser GPL) license.

FAnim
Timeline

This module implements a timeline window for GIMP, this timeline will help with
frame by frame animations.

"""
from gimpfu import *
import pygtk
pygtk.require('2.0')
import gtk, array, time, os, json

WINDOW_TITLE = "GIMP FAnim Timeline [%s]"
VERSION = 1.0
# general info
AUTHORS = [
        "Douglas Knowman <douglasknowman@gmail.com>"
        ]
NAME = "FAnim Timeline " + str(VERSION)
COPYRIGHT = "Copyright (C) 2016 \nDouglas Knowman"
WEBSITE = "https://github.com/douglasknowman/gimp-fanim"

# fixed frames prefix in the end to store visibility fix for the playback understand.
PREFIX="_fix"

# playback macros
NEXT = 1
PREV = 2
END = 3
START = 4
NOWHERE = 5
POS = 6
GIMP_ACTIVE = 7

# settings variable macros
WIN_WIDTH = "win_width"
WIN_HEIGHT = "win_height"
WIN_POSX = "win_posx"
WIN_POSY = "win_posy"
FRAMERATE = "framerate"
OSKIN_DEPTH = "oskin_depth"
OSKIN_ONPLAY = "oskin_onplay"
OSKIN_FORWARD = "oskin_forward"
OSKIN_BACKWARD = "oskin_backward"

# state to disable the buttons
PLAYING = 1
NO_FRAMES = 2

class Utils:

    @staticmethod
    def add_fixed_prefix(layer):
        """
        add the prefix at the end of the layer name to store if the frae is 
        visibly fixed or not.
        """
        if Utils.is_frame_fixed(layer): return
        layer.name = layer.name + PREFIX

    @staticmethod
    def rem_fixed_prefix(layer):
        """
        remove the prefix at the end of the layer name to store if the frae is 
        visibly fixed or not.
        """
        if not Utils.is_frame_fixed(layer): return
        layer.name = layer.name[:-4]


    @staticmethod
    def is_frame_fixed(layer):
        """
        get if the frame is visibly fixed or not based on the name of the layer.
        """
        name = layer.name
        return name[-4:] == PREFIX

    @staticmethod
    def button_stock(stock,size):
        """
        Return a button with a image from stock items.
        """
        b = gtk.Button()
        img = gtk.Image()
        img.set_from_stock(stock,size)
        b.set_image(img)
        return b

    @staticmethod
    def toggle_button_stock(stock,size):
        """
        Return a button with a image from stock items 
        """
        b = gtk.ToggleButton()
        img = gtk.Image()
        img.set_from_stock(stock,size)
        b.set_image(img)
        return b

    @staticmethod
    def spin_button(name="variable",number_type="int",value=0,min=1,max=100,advance=1):
        adjustment = gtk.Adjustment(value,min,max,advance,advance)
        digits = 0
        if number_type != "int":
            digits = 3
        l = gtk.Label(name)
        b = gtk.SpinButton(adjustment,0,digits)

        h = gtk.HBox()
        h.pack_start(l)
        h.pack_start(b)
        return h,adjustment

    @staticmethod
    def load_conffile(filename):
        """
        Load configuration from a file stored in gimp user folder.
        """
        directory = gimp.directory + "/fanim"
        if not os.path.exists(directory):
            os.mkdir(directory)

        filepath = directory + "/" + filename
        if os.path.exists(filepath):
            f = open(filepath,'r')
            dic = json.load(f)
            f.close()
            return dic

        else:
            return None

    @staticmethod
    def save_conffile(filename,conf={}):
        """
        Save a configuration dictionary in a json file on user folder.
        """
        directory = gimp.directory + "/fanim"
        if not os.path.exists(directory):
            os.mkdir(directory)

        filepath = directory + "/" + filename
        f = open(filepath,'w')
        json.dump(conf,f)
        f.close()
        


class ConfDialog(gtk.Dialog):
    """
    Create a configuration dialog to the user change the variables.
    """
    def __init__(self,title="Config",parent=None,config = None):
        gtk.Dialog.__init__(self,title,parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                ('Apply',gtk.RESPONSE_APPLY,'Cancel',gtk.RESPONSE_CANCEL))

        self.set_keep_above(True)
        self.set_position(gtk.WIN_POS_CENTER)

        self.last_config= config # settings 
        self.atual_config = config

        # setup all widgets
        self._setup_widgets()

    def update_config(self,widget,var_type=None):
        if isinstance(widget,gtk.Adjustment):
            value = widget.get_value()
        elif isinstance(widget,gtk.CheckButton):
            value = widget.get_active()
        self.atual_config[var_type] = value

    def _setup_widgets(self):

        h_space = 4 # horizontal space

        # create the frames to contein the diferent settings.
        f_time = gtk.Frame(label="Time")
        f_oskin = gtk.Frame(label="Onion Skin")
        self.set_size_request(300,-1)
        self.vbox.pack_start(f_time,True,True,h_space)
        self.vbox.pack_start(f_oskin,True,True,h_space)

        # create the time settings.
        th = gtk.HBox()
        fps,fps_spin = Utils.spin_button("Framerate",'int',self.last_config[FRAMERATE],1,100) #conf fps

        th.pack_start(fps,True,True,h_space)

        f_time.add(th)
        # create onion skin settings
        ov = gtk.VBox()
        f_oskin.add(ov)
        
        # fist line
        oh1 = gtk.HBox()
        depth,depth_spin = Utils.spin_button("Depth",'int',self.last_config[OSKIN_DEPTH],1,4,1) #conf depth

        on_play = gtk.CheckButton("On Play")
        on_play.set_active(self.last_config[OSKIN_ONPLAY])

        oh1.pack_start(depth,True,True,h_space)
        oh1.pack_start(on_play,True,True,h_space)
        ov.pack_start(oh1)
        # second line
        oh2 = gtk.HBox()
        forward = gtk.CheckButton("Forward")
        forward.set_active(self.last_config[OSKIN_FORWARD])

        backward = gtk.CheckButton("Backward")
        backward.set_active(self.last_config[OSKIN_BACKWARD])

        oh2.pack_start(forward,True,True,h_space)
        oh2.pack_start(backward,True,True,h_space)

        ov.pack_start(oh2)
        # last line

        # connect a callback to all
        
        fps_spin.connect("value_changed",self.update_config,FRAMERATE)
        depth_spin.connect("value_changed",self.update_config,OSKIN_DEPTH)
        on_play.connect("toggled",self.update_config,OSKIN_ONPLAY)
        forward.connect("toggled",self.update_config,OSKIN_FORWARD)
        backward.connect("toggled",self.update_config,OSKIN_BACKWARD)

        # show all
        self.show_all()

    def run(self):
        result = super(ConfDialog,self).run()
        conf = self.last_config

        if result == gtk.RESPONSE_APPLY:
            conf = self.atual_config

        return result, conf

class Player():
    """
    This class will implement a loop to play the frames through time, after
    play each frame, a gtk event handler is called to not freaze the UI.
    """
    def __init__(self,timeline,play_button):

        self.timeline = timeline
        self.play_button = play_button
        self.cnt = 0

    def start(self):
        
        while  self.timeline.is_playing:
            time.sleep(1.0/self.timeline.framerate)

            self.timeline.on_goto(None,NEXT)

            # while has fixed frames jump to the next
            while self.timeline.frames[self.timeline.active].fixed:
                if not self.timeline.is_replay and self.timeline.active >= len(self.timeline.frames)-1:
                    self.timeline.on_toggle_play(self.play_button)

                self.timeline.on_goto(None,NEXT)

            # if all frames is already played, and is no replay, stop the loop.
            if not self.timeline.is_replay and self.timeline.active >= len(self.timeline.frames)-1:
                self.timeline.on_toggle_play(self.play_button)

            # call gtk event handler.
            while gtk.events_pending():
                gtk.main_iteration()


class AnimFrame(gtk.EventBox):
    """
    A Frame representation for gtk.
    """
    def __init__(self,layer,width=100,height=120):
        gtk.EventBox.__init__(self)
        self.set_size_request(width,height)
        #variables
        self.thumbnail = None
        self.label = None
        self.layer = layer
        self.fixed = False

        self._fix_button_images = []
        self._fix_button = None
        self._setup()

    def highlight(self,state):
        if state:
            self.set_state(gtk.STATE_SELECTED)
        else :
            self.set_state(gtk.STATE_NORMAL)

    def on_toggle_fix(self,widget):
        self.fixed = widget.get_active()
        if widget.get_active():
            Utils.add_fixed_prefix(self.layer)
            self._fix_button.set_image(self._fix_button_images[0])
        else:
            Utils.rem_fixed_prefix(self.layer)
            self._fix_button.set_image(self._fix_button_images[1])

    def _setup(self):
        self.thumbnail = gtk.Image()
        self.label = gtk.Label(self.layer.name)
        # creating the fix button, to anchor background frames.
        self._fix_button = Utils.toggle_button_stock(gtk.STOCK_MEDIA_RECORD,20)
        self._fix_button.set_tooltip_text("toggle fixed visibility.")

        # update fixed variable
        self.fixed = Utils.is_frame_fixed(self.layer)
        #images
        pin_img = gtk.Image()
        pin_img.set_from_stock(gtk.STOCK_YES,20)
        pin_img2 = gtk.Image()
        pin_img2.set_from_stock(gtk.STOCK_MEDIA_RECORD,20)

        self._fix_button_images = [pin_img,pin_img2]

        ## connect
        self._fix_button.connect('clicked',self.on_toggle_fix)

        if self.fixed:
            self._fix_button.set_image(self._fix_button_images[0])
            self._fix_button.set_active(True)
        else :
            self._fix_button.set_image(self._fix_button_images[1])
            self._fix_button.set_active(False)

        frame = gtk.Frame()
        layout = gtk.VBox()
        # add frame to this widget
        self.add(frame)

        # add layout manager to the frame
        frame.add(layout)

        layout.pack_start(self.label)
        layout.pack_start(self._fix_button)
        layout.pack_start(self.thumbnail)
        self._get_thumb_image()

    def _get_thumb_image(self):
        """
        convert the pixel info returned by python into a gtk image to be
        showed.
        """
        width = 100
        height = 100
        image_data = pdb.gimp_drawable_thumbnail(self.layer,width,height)

        w,h,c,data = image_data[0],image_data[1],image_data[2],image_data[4]

        # create a array of unsigned 8bit data.
        image_array = array.array('B',data)

        pixbuf = gtk.gdk.pixbuf_new_from_data(image_array,gtk.gdk.COLORSPACE_RGB,c>3,8,w,h,w*c)
        self.thumbnail.set_from_pixbuf(pixbuf)

    def update_layer_info(self):
        self._get_thumb_image()

class Timeline(gtk.Window):
    def __init__(self,title,image):
        gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)

        self.set_title(title)
        self.image = image
        self.frame_bar = None
        # variables
        self.is_playing = False
        self.is_replay = False
        # modifiable widgets
        self.play_button_images = []
        self.widgets_to_disable = [] # widgets to disable when playing
        self.play_bar = None
        
        # frames
        self.frames = [] # all frame widgets
        self.active = None  # active frame / gimp layer
        self.before_play = None # active frame before play

        self.framerate = 30

        # new frame.
        self.new_layer_type = TRANSPARENT_FILL

        # onionskin variables
        self.oskin = False
        self.oskin_depth = 2
        self.oskin_backward = True
        self.oskin_forward = False
        self.oskin_opacity = 50.0
        self.oskin_opacity_decay = 20.0
        self.oskin_onplay= True

        self.player = None

        # gtk window
        self.win_pos = (20,20)
        self.win_size = (200,200)
        # create all widgets
        self._setup_widgets()

    def destroy(self,widget):
        # if is closing and still playing turn off.
        if self.is_playing:
            #self.on_toggle_play(None)
            self.is_playing = False
        self.on_goto(None,START)

        #save the settings before quit.
        Utils.save_conffile("conf.json",self.get_settings())

        gtk.main_quit()

    def start(self):
        gtk.main()

    def _get_theme_gtkrc(self,themerc):
        rcpath = ""
        with  open(themerc,'r') as trc:
            for l in trc.readlines():
                if l[:7] == "include":
                    rcpath = l[9:-2]
                    break
        return rcpath

    def on_window_resize(self,*args):
        # update the window position  to save later on.
        self.win_pos = self.get_position()

    def _setup_widgets(self):
        """
        create all the window staticaly placed widgets.
        """
        #load the saved setting before start.
        self.set_settings(Utils.load_conffile("conf.json"))

        # basic window definitions
        self.connect("destroy",self.destroy)
        self.connect("focus_in_event",self.on_window_focus)
        self.connect("configure_event",self.on_window_resize)

        self.set_default_size(self.win_size[0],self.win_size[1])
        self.set_keep_above(True)
        
        #self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.move(self.win_pos[0],self.win_pos[1])

        # parse gimp theme gtkrc
        gtkrc_path  = self._get_theme_gtkrc(gimp.personal_rc_file('themerc'))

        if  os.name != 'nt':# try apply the theme by parse a gtkrc file if is not a windows system.
            gtk.rc_parse(gtkrc_path)
        else: # if error occur them parse the file in another way.
            gtk.rc_add_default_file(gtkrc_path)
            gtk.rc_reparse_all()

        # start creating basic layout
        base = gtk.VBox()

        # commands bar widgets
        cbar = gtk.HBox()
        cbar.pack_start(self._setup_playbackbar(),False,False,10)
        cbar.pack_start(self._setup_editbar(),False,False,10)
        cbar.pack_start(self._setup_onionskin(),False,False,10)
        cbar.pack_start(self._setup_config(),False,False,10)
        cbar.pack_start(self._setup_generalbar(),False,False,10)

        # frames bar widgets
        self.frame_bar = gtk.HBox()
        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        scroll_window.add_with_viewport(self.frame_bar)
        scroll_window.set_size_request(-1,140)

        # mount the widgets together
        base.pack_start(cbar,False,False,0)
        base.pack_start(scroll_window,True,True,0)
        self.add(base)
        
        # catch all layers
        self._scan_image_layers()
        self.active = 0
        self.on_goto(None,GIMP_ACTIVE)

        # finalize showing all widgets
        self.show_all()

    def _scan_image_layers(self):
        """
        If exists frames this function destroys all, after that the image layers
        is scanned and the frames are recreated.
        """
        layers = self.image.layers

        if self.frames:
            for frame in self.frames:
                self.frame_bar.remove(frame)
                frame.destroy()
            self.frames = []

        #layers.reverse()
        for layer in layers:
            f = AnimFrame(layer)
            f.connect("button_press_event",self.on_click_goto)
            self.frame_bar.pack_start(f,False,True,2)
            self.frames.append(f)
            f.show_all()

        #if len(self.frames) > 0:
        #    self.active = 0
        #    self.on_goto(None,START)

    def _setup_playbackbar(self):
        playback_bar = gtk.HBox()
        button_size = 30
        stock_size = gtk.ICON_SIZE_BUTTON

        # play button
        ## image
        image_play = gtk.Image()
        image_play.set_from_stock(gtk.STOCK_MEDIA_PLAY,stock_size)
        image_pause = gtk.Image()
        image_pause.set_from_stock(gtk.STOCK_MEDIA_PAUSE,stock_size)
        ## append the images to a list to be used later on
        self.play_button_images.append(image_play)
        self.play_button_images.append(image_pause)
        ## button
        b_play = gtk.Button()
        b_play.set_image(image_play)
        b_play.set_size_request(button_size,button_size)

        b_tostart = Utils.button_stock(gtk.STOCK_MEDIA_PREVIOUS,stock_size)
        b_toend = Utils.button_stock(gtk.STOCK_MEDIA_NEXT,stock_size)
        b_prev = Utils.button_stock(gtk.STOCK_MEDIA_REWIND,stock_size)
        b_next = Utils.button_stock(gtk.STOCK_MEDIA_FORWARD,stock_size)

        b_repeat = Utils.toggle_button_stock(gtk.STOCK_REFRESH,stock_size)

        # connecting the button with callback
        b_play.connect('clicked',self.on_toggle_play)
        b_repeat.connect('toggled',self.on_replay)

        b_next.connect('clicked',self.on_goto,NEXT,True)
        b_prev.connect('clicked',self.on_goto,PREV,True)
        b_toend.connect('clicked',self.on_goto,END,True)
        b_tostart.connect('clicked',self.on_goto,START,True)


        # add to the disable on play list
        w = [b_repeat,b_prev,b_next,b_tostart,b_toend]
        map(lambda x: self.widgets_to_disable.append(x),w)
        self.play_bar = playback_bar

        # set the tooltips
        b_play.set_tooltip_text("Animation play/pause")
        b_repeat.set_tooltip_text("Animation replay active/deactive")
        b_prev.set_tooltip_text("To the previous frame")
        b_next.set_tooltip_text("To the next frame")
        b_tostart.set_tooltip_text("To the start frame")
        b_toend.set_tooltip_text("To the end frame")
        
        # packing everything in gbar
        playback_bar.pack_start(b_tostart,False,False,0)
        playback_bar.pack_start(b_prev,False,False,0)
        playback_bar.pack_start(b_play,False,False,0)
        playback_bar.pack_start(b_next,False,False,0)
        playback_bar.pack_start(b_toend,False,False,0)
        playback_bar.pack_start(b_repeat,False,False,0)

        return playback_bar

    def _setup_editbar(self):
        stock_size = gtk.ICON_SIZE_BUTTON
        edit_bar = gtk.HBox()
        
        b_back = Utils.button_stock(gtk.STOCK_GO_BACK,stock_size)
        b_forward = Utils.button_stock(gtk.STOCK_GO_FORWARD,stock_size)
        b_rem = Utils.button_stock(gtk.STOCK_REMOVE,stock_size)
        b_add = Utils.button_stock(gtk.STOCK_ADD,stock_size)
        b_copy = Utils.button_stock(gtk.STOCK_COPY,stock_size)

        # add to the disable on play list
        w = [b_back,b_forward,b_rem,b_add,b_copy]
        map(lambda x: self.widgets_to_disable.append(x),w)

        # connect callbacks:
        b_rem.connect("clicked",self.on_remove) # remove frame
        b_add.connect("clicked",self.on_add) # add frame
        b_copy.connect("clicked",self.on_add,True) # add frame
        b_back.connect("clicked",self.on_move,PREV)
        b_forward.connect("clicked",self.on_move,NEXT)

        # tooltips
        b_rem.set_tooltip_text("Remove a frame/layer")
        b_add.set_tooltip_text("Add a frame/layer")
        b_copy.set_tooltip_text("Duplicate the atual selected frame")
        b_back.set_tooltip_text("Move the atual selected frame backward")
        b_forward.set_tooltip_text("Move the atual selected frame forward")

        # packing everything in gbar
        map(lambda x: edit_bar.pack_start(x,False,False,0),w)

        return edit_bar

    def _setup_config(self):
        stock_size = gtk.ICON_SIZE_BUTTON
        config_bar = gtk.HBox()

        b_conf = Utils.button_stock(gtk.STOCK_PREFERENCES,stock_size)

        self.widgets_to_disable.append(b_conf)
        # connect
        b_conf.connect("clicked",self.on_config)

        # tooltips
        b_conf.set_tooltip_text("open configuration dialog")

        config_bar.pack_start(b_conf,False,False,0)
        return config_bar

    def _setup_onionskin(self):
        stock_size = gtk.ICON_SIZE_BUTTON
        button_size = 30
        onionskin_bar = gtk.HBox()

        # active onionskin
        b_active = Utils.toggle_button_stock(gtk.STOCK_DND_MULTIPLE,stock_size)

        # connect widgets
        b_active.connect("clicked",self.on_onionskin)

        # tooltips
        b_active.set_tooltip_text("enable/disable the onion skin effect")

        # add to the disable on play list
        w = [b_active]
        map(lambda x: self.widgets_to_disable.append(x),w)

        # packing everything in gbar
        map(lambda x: onionskin_bar.pack_start(x,False,False,0),w)

        return onionskin_bar

    def _setup_generalbar(self):
        stock_size = gtk.ICON_SIZE_BUTTON
        general_bar = gtk.HBox()

        b_about = Utils.button_stock(gtk.STOCK_ABOUT,stock_size)

        b_to_gif = Utils.button_stock(gtk.STOCK_CONVERT,stock_size)
        b_to_sprite = Utils.button_stock(gtk.STOCK_MISSING_IMAGE,stock_size)

        # TODO implement export button
        
        b_quit = Utils.button_stock(gtk.STOCK_QUIT,stock_size)

        # callbacks
        b_quit.connect('clicked',self.destroy)
        b_about.connect('clicked',self.on_about)

        b_to_gif.connect('clicked',self.create_formated_version,'gif')
        b_to_sprite.connect('clicked',self.create_formated_version,'spritesheet')

        # tooltips
        b_about.set_tooltip_text("About FAnim")
        b_quit.set_tooltip_text("Exit")
        b_to_gif.set_tooltip_text("Create a formated Image to export as gif animation")
        b_to_sprite.set_tooltip_text("Create a formated Image to export as spritesheet")

        # add to the disable on play list
        w = [b_about, b_to_gif,b_to_sprite, b_quit]
        map(lambda x: self.widgets_to_disable.append(x),w)

        # packing everything in gbar
        map(lambda x: general_bar.pack_start(x,False,False,0),w)

        return general_bar

    def get_settings(self):
        s = {}
        s[FRAMERATE] = self.framerate
        s[OSKIN_DEPTH] = self.oskin_depth
        s[OSKIN_FORWARD] = self.oskin_forward
        s[OSKIN_BACKWARD] = self.oskin_backward
        s[OSKIN_ONPLAY] = self.oskin_onplay

        s[WIN_POSX] = self.win_pos[0]
        s[WIN_POSY] = self.win_pos[1]
        s[WIN_WIDTH] = self.get_allocation()[2]
        s[WIN_HEIGHT] = self.get_allocation()[3]
        return s

    def set_settings(self,conf):
        if conf == None:
            return

        self.framerate = int(conf[FRAMERATE])
        self.oskin_depth = int(conf[OSKIN_DEPTH])
        self.oskin_forward = conf[OSKIN_FORWARD]
        self.oskin_backward = conf[OSKIN_BACKWARD]
        self.oskin_onplay = conf[OSKIN_ONPLAY]
        self.win_size  = (conf[WIN_WIDTH],conf[WIN_HEIGHT])
        self.win_pos = (conf[WIN_POSX],conf[WIN_POSY])

    def _toggle_enable_buttons(self,state):
        if state == PLAYING:
            for w in self.widgets_to_disable:
                w.set_sensitive(not self.is_playing)
        elif state == NO_FRAMES:
            self.play_bar.set_sensitive(not self.play_bar.get_sensitive())


#----------------------Callback Functions----------------#
    def on_window_focus(self,widget,other):
        """
        Update all timeline thumbnails.
        """
        self._scan_image_layers()
        self.on_goto(None,GIMP_ACTIVE)

    def on_about(self,widget):
        about = gtk.AboutDialog()

        about.set_authors(AUTHORS)
        about.set_program_name(NAME)
        about.set_copyright(COPYRIGHT)
        about.set_website(WEBSITE)

        about.run()
        about.destroy()

    def create_formated_version(self,widget,format='gif'):
        """
        create a formated version of the animation to export as a giff or as a spritesheet.
        """
        # get normal and visibly fixed layers.
        frame_layers = filter(lambda x: x.fixed == False,self.frames)
        fixed_layers = filter(lambda x: x.fixed == True,self.frames)

        new_image = gimp.Image(self.image.width,self.image.height,self.image.base_type)

        # reversed frame layers.
        r_frame_layers = frame_layers
        r_frame_layers.reverse()

        for fl in r_frame_layers:
            group = gimp.GroupLayer(new_image,fl.layer.name)
            
            lcopy = pdb.gimp_layer_new_from_drawable(fl.layer,new_image)
            lcopy.visible = True

            new_image.add_layer(group,len(new_image.layers))
            new_image.insert_layer(lcopy,group,0)

            # get the background and foreground frames.
            up_fixed = filter(lambda x: self.frames.index(x) < self.frames.index(fl),fixed_layers)
            bottom_fixed = filter(lambda x: self.frames.index(x) > self.frames.index(fl),fixed_layers)

            # copy and insert bg and fg frames.
            cnt = 0
            for ff in fixed_layers:
                copy = pdb.gimp_layer_new_from_drawable(ff.layer,new_image)
                if ff in up_fixed:
                    new_image.insert_layer(copy,group,cnt)
                    cnt +=1
                if ff in bottom_fixed:
                    new_image.insert_layer(copy,group,len(group.layers))

        # show the image in a gimp display.
        gimp.Display(new_image)

    def on_toggle_play(self,widget):
        """
        This method change the animation play state,
        change the button image and will disable/enable the other buttons
        interation.
        for that they need 2 image which is stored in self.play_button_images
        variable.
        """
        # if onionskin on play is disable then disable remaining frames
        if self.oskin_onplay:
            self.layers_show(False)

        self.is_playing = not self.is_playing

        if self.is_playing:
            # saving the atual frame before start to play.
            if self.before_play == None:
                self.before_play = self.active

            widget.set_image(self.play_button_images[1]) # set pause image to the button

            # start the player object to play the frames in a sequence.
            if not self.player:
                self.player = Player(self,widget)
            # block every other button than pause.
            self._toggle_enable_buttons(PLAYING)

            # start the loop to play the frames.
            self.player.start()

        else :
            # restore last frame before play.
            if self.before_play != None:
                self.on_goto(None,POS,index=self.before_play)
                self.before_play = None

            widget.set_image(self.play_button_images[0]) # set play image
            self._toggle_enable_buttons(PLAYING)
            self.on_goto(None,NOWHERE) # update atual frame.

    def on_replay(self,widget):
        self.is_replay = widget.get_active()

    def on_onionskin(self,widget):
        """
        Toggle onionskin.
        """
        self.layers_show(False) # clear remaining onionskin frames
        self.oskin = widget.get_active()
        self.on_goto(None,NOWHERE,True)

    def on_config(self,widget):
        """
        Open a dialog to set all the settings of the plugin.
        """
        dialog = ConfDialog("FAnim Config",self,self.get_settings())
        result, config = dialog.run()

        if result == gtk.RESPONSE_APPLY:
            self.set_settings(config)
        dialog.destroy()

    def on_move(self,widget,direction):
        """
        Move the layer and the frame forward or backward.
        """
        # calculate next position
        index = 0
        if direction == NEXT:
            index = self.active+1
            if index == len(self.frames):
                return

        elif direction == PREV:
            index = self.active-1
            if self.active-1 < 0:
                return
        # move layer.
        if direction == PREV:
            self.image.raise_layer(self.frames[self.active].layer)
        elif direction == NEXT:
            self.image.lower_layer(self.frames[self.active].layer)

        # update Timeline
        self._scan_image_layers()
        self.active = index
        self.on_goto(None,NOWHERE)

    def on_remove(self,widget):
        """
        Remove the atual selected frame, and his layer. and if the case his sublayers.
        """
        if not self.frames:
            return 

        if self.active > 0:
            self.on_goto(None,PREV,True)

        index = self.active + 1
        if self.active == 0:
            index = self.active

        self.image.remove_layer(self.frames[index].layer)
        self.frame_bar.remove (self.frames[index])
        self.frames[index].destroy()
        self.frames.remove(self.frames[index])

        if len(self.frames) == 0:
            self._toggle_enable_buttons(NO_FRAMES)
        else :
            self.on_goto(None,None,True)

    def on_add(self,widget,copy=False):
        """
        Add new layer to the image and a new frame to the Timeline.
        if copy is true them the current layer will be copy.
        """
        # starting gimp undo group
        self.image.undo_group_start()

        name = "Frame " + str(len(self.frames))
        # create the layer to add
        l = None
        if not copy:
            l = gimp.Layer(self.image,name, self.image.width,self.image.height,RGBA_IMAGE,100,NORMAL_MODE)

        else: # copy current layer to add
            l = self.frames[self.active].layer.copy()
            l.name = name

        # adding layer
        self.image.add_layer(l,self.active+1)
        if self.new_layer_type == TRANSPARENT_FILL and not copy:
            pdb.gimp_edit_clear(l)

        self._scan_image_layers()
        self.on_goto(None,NEXT,True)

        if len(self.frames) == 1 :
            self._toggle_enable_buttons(NO_FRAMES)

        # ending gimp undo group
        self.image.undo_group_end()

    def on_click_goto(self,widget,event):
        """
        handlers a click on frame widgets.
        """
        i = self.frames.index(widget)
        self.on_goto(None,POS,index=i)

    def on_goto(self,widget,to,update=False,index=0):
        """
        This method change the atual active frame to when the variable
        (to) indicate, the macros are (START, END, NEXT, PREV,POS,GIMP_ACTIVE)
        - called once per frame when is_playing is enabled.
        """

        self.layers_show(False)

        if update:
            self.frames[self.active].update_layer_info()

        if to == START:
            self.active = 0

        elif to == END:
            self.active = len(self.frames)-1

        elif to == NEXT:
            i = self.active + 1
            if i > len(self.frames)-1:
                i = 0
            self.active = i

        elif to == PREV:
            i = self.active - 1
            if i < 0:
                i= len(self.frames)-1
            self.active = i
        elif to == POS:
            self.active = index

        elif to == GIMP_ACTIVE:
            self.active = self.image.layers.index(self.image.active_layer)

        self.layers_show(True)
        self.image.active_layer = self.frames[self.active].layer

        gimp.displays_flush() # update the gimp GUI


    def layers_show(self,state):
        """
        Util function to hide the old frames and show the next.
        """
        self.image.undo_freeze()

        opacity = 0

        self.frames[self.active].layer.opacity = 100.0

        if not state:
            opacity = 100.0
        else :
            opacity = self.oskin_opacity

        self.frames[self.active].layer.visible = state # show or hide the frame
        self.frames[self.active].highlight(state) # highlight or not the frame

        if self.oskin and not(self.is_playing and not self.oskin_onplay) :
            # calculating the onionskin backward and forward
            for i in range(1,self.oskin_depth +1):

                if self.oskin_backward:
                    pos = self.active - i
                    if self.frames[pos].fixed: break #discard fixed frames

                    if pos >= 0:
                        # calculate onionskin depth opacity decay.
                        o = opacity - i * self.oskin_opacity_decay
                        self.frames[pos].layer.visible = state
                        self.frames[pos].layer.opacity = o

                if self.oskin_forward:
                    pos = self.active +i
                    if self.frames[pos].fixed: break  #discard fixed frames

                    self.frames[self.active].layer.opacity = opacity

                    if pos <= len(self.frames)-1:
                        # calculate onionskin depth opacity decay.
                        o = opacity - i * self.oskin_opacity_decay
                        self.frames[pos].layer.visible = state
                        self.frames[pos].layer.opacity = o

        # freese the gimp undo system.
        if self.frames[self.active].fixed and state == False:
            self.frames[self.active].layer.visible = True

        # unfreese the gimp undo system.
        self.image.undo_thaw()


def timeline_main(image,drawable):
    """
    gimp call initial function, created the main timeline window.
    """
    global WINDOW_TITLE
    WINDOW_TITLE = WINDOW_TITLE % (image.name)
    win = Timeline(WINDOW_TITLE,image)
    win.start()
