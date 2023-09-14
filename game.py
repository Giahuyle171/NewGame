"""
----------------------------
 Project started on 7-7-2023
 Coder:  Le Chau Gia Huy
----------------------------
"""
import pygame
import json
import sys
import base64
from io import BytesIO
import random

class Data:
	def __init__(self):
		self.settings = {}
		self.userdata = {}
		self.media = {}
		self.language = {}
		self.rect = {}
		self.paths = {
			"settings": "settings.json",
			"userdata": "userdata.json",
			"media": "media.json",
			"language_vi": "./language/language_vi",
			"language_en": "./language/language_en",
			"rect": "rect.json"
		}
		self.loadSettings()
		self.loadUserdata()
		self.fixUserdata()
		self.updateUserdata()
		self.loadMedia()
		self.loadLanguage()
		self.loadRect()

	def loadSettings(self):
		with open(self.paths["settings"], "r") as file:
			self.settings = json.loads(file.read())

	def loadUserdata(self):
		try:
			with open(self.paths["userdata"], "r") as file:
				self.userdata = json.loads(file.read())
		except:
			self.userdata = {}

	def updateUserdata(self):
		with open(self.paths["userdata"], "w") as file:
			file.write(json.dumps(self.userdata, indent=4))

	def fixUserdata(self):
		# Check resolution screen
		resolution = pygame.display.get_desktop_sizes()[0]
		ratio = self.settings["ui"]["screen_ratio"][0]/self.settings["ui"]["screen_ratio"][1]
		factor = 0.8
		if "screensize" not in self.userdata or len(self.userdata["screensize"]) != 2:
			if resolution[0]/resolution[1] >= ratio:
				self.userdata["screensize"] = [factor*resolution[1]*ratio, factor*resolution[1]]
			else:
				self.userdata["screensize"] = [factor*resolution[0], factor*resolution[0]/ratio]
				
		# Fix other object
		stack = [(self.settings["userdata"], self.userdata)]
		while stack:
			form, dicts = stack.pop()
			for key in form:
				if key not in dicts or type(form[key]) != type(dicts[key]):
					dicts[key] = form[key]
				elif isinstance(form[key], list):
					if len(form[key]) != len(dicts[key]):
						dicts[key] = form[key]
					elif any(type(x) != type(y) for x,y in zip(form[key],dicts[key])):
						dicts[key] = form[key]
				elif isinstance(form[key], dict):
					stack.append((form[key], dicts[key]))

	def loadMedia(self):
		with open(self.paths["media"], "r") as file:
			self.media = json.loads(file.read())
		stack = [self.media]
		while stack:
			item = stack.pop()
			for key in item:
				if isinstance(item[key], dict):
					stack.append(item[key])
				elif isinstance(item[key], str):
					item[key] = base64.b64decode(item[key])
				elif isinstance(item[key], list):
					for i in range(len(item[key])):
						item[key][i] = base64.b64decode(item[key][i])

	def loadLanguage(self):
		with open(self.paths["language_"+self.userdata["language"]], "r") as file:
			language = file.read()
		for line in language.splitlines():
			key, values = line.split("=")
			self.language[key.strip()] = values.strip()[1:-1]

	def loadRect(self):
		with open(self.paths["rect"], "r") as file:
			self.rect = json.loads(file.read())
		element = {
			'topleft', 'bottomleft', 'topright', 'bottomright', 
			'midtop', 'midleft', 'midbottom', 'midright',
			'center'
		}
		size = self.userdata["screensize"]
		ratio = self.settings["ui"]["screen_ratio"][0]/self.settings["ui"]["screen_ratio"][1]
		stdsize = [size[1]*ratio, size[1]]
		stack = [(self.rect, size)]
		while stack:
			item, size = stack.pop()
			for key in item:
				if isinstance(item[key], dict):
					stack.append((item[key], item.get("size", size)))
				elif key in element:
					item[key] = [x*y for x, y in zip(item[key], size)]
				elif key == "size":
					item[key] = [x*y for x, y in zip(item[key], stdsize)]

class SurfaceManager:
	def __init__(self, event=True, update=True, status=True):
		self.__event = event
		self.__update = update
		self.__status = status
	@property
	def _event(self):
		return self.__event
	@property
	def _update(self):
		return self.__update
	@property
	def _status(self):
		return self.__status
	def start_event(self):
		self.__event = True
	def pause_event(self):
		self.__event = False
	def start_update(self):
		self.__update = True
	def pause_update(self):
		self.__update = False
	def start(self):
		self.__status = True
	def pause(self):
		self.__status = False

class Timer:
	def __init__(self, cooldown):
		self.cooldown = cooldown
		self.total = 0
		self.prev = 0
		self.start = True
	def start(self):
		self.start = True
		self.prev = pygame.time.get_ticks() - self.total
	def pause(self):
		self.start = False
	def update(self):
		if not self.start: return False
		cur = pygame.time.get_ticks()
		if not self.prev: self.prev = cur
		self.total += cur - self.prev
		self.prev = cur
		if self.total >= self.cooldown:
			self.total = 0
			return True

class Audio:
	def __init__(self, settings, media):
		self.data = {}
		self.settings = settings
		self.media = media
		self.volume = 1

	def load(self, *keys):
		for k in keys if keys else self.settings.keys():
			if isinstance(self.settings[k], dict):
				self.data[k] = Audio(self.settings[k], self.media)
				self.data[k].load()
			elif isinstance(self.settings[k], list):
				self.data[k] = pygame.mixer.Sound(BytesIO(self.media[self.settings[k][0]]))
				self.data[k].set_volume(self.volume*self.settings[k][1])

	def set_volume(self, volume):
		self.volume = volume
		for k, v in self.data.items():
			if isinstance(v, type(self)):
				v.set_volume(self.volume)
			else:
				v.set_volume(self.volume*self.settings[k][1])

	def remove(self, *keys):
		for k in keys: self.data.pop(k)

	def __getattr__(self, key):
		return self.data[key]

	def __str__(self):
		return "Audio({})".format(", ".join([f"{k}: {v}" for k,v in self.data.items()]))

class Attr:
	def __init__(self, **kwargs):
		self.add(**kwargs)
	def __setattr__(self, key, value):
		self.__dict__[key] = value
	def __delattr__(self, key):
		self.__dict__.pop(key)
	def __str__(self):
		return "{{{}}}".format(", ".join([f"{k}: {v}" for k,v in self.__dict__.items()]))
	def remove(self, *keys):
		for k in keys: self.__dict__.pop(key)
	def add(self, **kwargs):
		self.__dict__.update(kwargs)

class Game:
	def __init__(self):
		global data, Surfaces, audio
		pygame.init()
		data = Data()
		pygame.display.set_caption(data.settings["ui"]["title"])
		pygame.display.set_mode(data.userdata["screensize"], vsync=int(data.userdata["vsync"]))
		self.clock = pygame.time.Clock()

		audio = Attr(
			music = Audio(data.settings["audio"]["music"], data.media)
		)
		audio.music.set_volume(data.userdata["music"])
		Surfaces = {}
		Surfaces.update(StartScreen=StartScreen(pygame.display.get_surface()))

	def loop(self):
		while True:
			self.clock.tick(data.userdata["fps"])

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				for surface in Surfaces.copy().values():
					if hasattr(surface, "event"):
						surface.event(event)

			for surface in Surfaces.copy().values(): 
				surface.draw()
			pygame.display.update()

class StartScreen(SurfaceManager):
	def __init__(self, surface):
		super().__init__()
		self.surface = surface
		self.settings = data.settings["ui"]["StartScreen"]
		# Background
		self.bg = pygame.image.load(BytesIO(data.media["startbg"])).convert_alpha()
		self.bg = pygame.transform.smoothscale_by(self.bg, self.surface.get_height()/self.bg.get_height())
		self.rectbg = self.bg.get_rect(center=self.surface.get_rect().center)
		# Create main menu
		self.pole = pygame.image.load(BytesIO(data.media["signboardpole"])).convert_alpha()
		self.pole = pygame.transform.smoothscale_by(
			self.pole, data.rect["signboardpole"]["size"][1]/self.pole.get_height()
		)
		self.rectpole = self.pole.get_rect()
		for k, v in data.rect["signboardpole"].items(): 
			if not isinstance(v, dict) and k != "size": setattr(self.rectpole, k, v)
		# Create button play, setting, credit
		self.menu = [pygame.image.load(BytesIO(s)).convert_alpha() for s in data.media["signboard"]]
		self.menuz = []
		self.rectmenu = []
		self.rectmenuz = []
		self.menufont = []
		self.textmenu = []
		for i, name in enumerate(["play", "setting", "credit"]):
			# Create Surface
			height = data.rect["button"+name]["size"][1]/self.menu[i].get_height()
			self.menuz.append(pygame.transform.smoothscale_by(self.menu[i], height*1.05))
			self.menu[i] = pygame.transform.smoothscale_by(self.menu[i], height)
			# Create rect
			self.rectmenu.append(self.menu[i].get_rect())
			for k, v in data.rect["button"+name].items():
				if not isinstance(v, dict) and k != "size": setattr(self.rectmenu[i], k, v)
			self.rectmenuz.append(self.menuz[i].get_rect(center=self.rectmenu[i].center))
			# Create font
			size = data.rect["button"+name]["text"]["size"][1]*self.settings["menu"]["textfactor"]
			self.menufont.append(pygame.freetype.Font(self.settings["menu"]["font"], size))
			# Render text
			self.textmenu.append(self.menufont[i].render(
				data.language[name.upper()+"_BUTTON"], self.settings["menu"]["textcolor"]
			))
			self.textmenu[i][1].center = self.rectmenu[i].center
		# Snow fall animation
		self.snowfall = Snowfall(self.surface)
		# Aduio
		audio.music.load("bg")
		audio.music.bg.play(-1)

	def event(self, event):
		if not self._event or not self._status: return
		posMouse = pygame.mouse.get_pos()
		if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			if self.rectmenu[0].collidepoint(posMouse):
				self.pause_update() if self._update else self.start_update() 
			elif self.rectmenu[1].collidepoint(posMouse):
				if "SettingScreen" not in Surfaces:
					Surfaces.update(SettingScreen=SettingScreen(self.surface))
				else:
					Surfaces["SettingScreen"].start()
				self.pause_event()
			elif self.rectmenu[2].collidepoint(posMouse):
				for key in Surfaces.copy():
					if key != "StartScreen": Surfaces.pop(key)
	def update(self):
		self.snowfall.update()
	def draw(self):
		if not self._status: return
		posMouse = pygame.mouse.get_pos()
		pressMouse = pygame.mouse.get_pressed()

		if self._update: self.update()
		# Draw
		self.surface.blit(self.bg, self.rectbg)
		self.snowfall.draw()
		# Draw menu
		self.surface.blit(self.pole, self.rectpole)
		for i in range(3):
			if self.rectmenu[i].collidepoint(posMouse) and not pressMouse[0] and self._event:
				self.surface.blit(self.menuz[i], self.rectmenuz[i])
			else:
				self.surface.blit(self.menu[i], self.rectmenu[i])
			self.surface.blit(self.textmenu[i][0], self.textmenu[i][1])

class SettingScreen(SurfaceManager):
	def __init__(self, surface):
		super().__init__()
		self.surface = surface
		self.settings = data.settings["ui"]["SettingScreen"]
		# Background
		self.bg = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
		self.bg.fill(self.settings["bgcolor"])
		# Board settings
		self.setboard = pygame.Surface(data.rect["settingboard"]["size"], pygame.SRCALPHA)
		self.rect = self.setboard.get_rect()
		for k, v in data.rect["settingboard"].items():
			if not isinstance(v, dict) and k != "size": setattr(self.rect, k, v)
		# Title
		self.titlefont = pygame.freetype.Font(
			self.settings["titlefont"],
			data.rect["settingboard"]["title"]["size"][1]*self.settings["titlefactor"]
		)
		self.title = self.titlefont.render(data.language["TITLE_SETTING_BOARD"], self.settings["titlecolor"])
		for k, v in data.rect["settingboard"]["title"].items():
			if not isinstance(v, dict) and k != "size": setattr(self.title[1], k, v)
		# Cancel button
		cancel = pygame.image.load(BytesIO(data.media["cancelbutton"])).convert_alpha()
		height = data.rect["settingboard"]["cancelbutton"]["size"][1]/cancel.get_height()
		self.cancel = [
			pygame.transform.smoothscale_by(cancel, height),
			pygame.transform.smoothscale_by(cancel, height*1.19)
		]
		self.rectcancel = [cancel.get_rect() for cancel in self.cancel]
		self.rectcancel[0].topright = (self.rect.w-self.rectcancel[0].w, self.rectcancel[0].h)
		self.rectcancel[1].center = self.rectcancel[0].center
		# Create audio settings
		rect = pygame.Rect((0,0), data.rect["settingboard"]["musicslider"]["size"])
		for k, v in data.rect["settingboard"]["musicslider"].items():
			if not isinstance(v, dict) and k != "size": setattr(rect, k, v)
		self.musicSlider = Slider(rect, self.settings["slidercolor"], (0,1))
		self.musicSlider.pos_mouse((-self.rect.x, -self.rect.y))
		self.musicSlider.level = data.userdata["music"]

	def event(self, event):
		if not self._event or not self._status: return
		posMouse = [x-y for x,y in zip(pygame.mouse.get_pos(), self.rect)]
		self.musicSlider.event(event)
		if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			if self.rectcancel[0].collidepoint(posMouse):
				Surfaces["StartScreen"].start_event()
				self.pause()

	def update(self):
		if self.musicSlider.level != data.userdata["music"]:
			data.userdata["music"] = self.musicSlider.level
			data.updateUserdata()
			audio.music.set_volume(data.userdata["music"])

	def draw(self):
		if not self._status: return
		posMouse = [x-y for x,y in zip(pygame.mouse.get_pos(), self.rect)]
		pressMouse = pygame.mouse.get_pressed()
		if self._update: self.update()
		# Draw backgorund
		self.surface.blit(self.bg, (0,0))
		# Draw setting board
		pygame.draw.rect(
			self.setboard, self.settings["setboardcolor"], ((0,0),self.rect.size),
			border_radius = self.rectcancel[0].h
		)
		# Draw cancel button
		if self.rectcancel[0].collidepoint(posMouse) and not pressMouse[0] and self._event:
			self.setboard.blit(self.cancel[1], self.rectcancel[1])
		else:
			self.setboard.blit(self.cancel[0], self.rectcancel[0])
		# Draw title
		self.setboard.blit(self.title[0], self.title[1])
		# Draw Music
		self.musicSlider.draw(self.setboard)
		self.surface.blit(self.setboard, self.rect)

class Slider:
	def __init__(self, rect, color, range):
		self.posMouse = (0,0)
		self.range = range
		self.active = False
		self.rect = pygame.Rect(rect)
		self.ctrack, self.cfill, self.chandle = color
		# Create track
		self.rtrack = self.rect.scale_by(1, 0.55)
		self.rtrack.center = self.rect.center
		self.track = renderRect(self.ctrack, self.rtrack.size, self.rtrack.h/2, 5)
		# Create fill
		self.rfill = self.rtrack.copy()
		self.rfill.w = self.rtrack.w/2 
		self.leftfill = renderRect(self.cfill, (self.rfill.h,self.rfill.h), self.rfill.h/2, 5)
		# Create handle
		self.handle = [
			renderCircle(self.chandle, self.rect.h/2, 4),
			renderCircle(self.chandle, self.rect.h/2*1.1, 4)
		]
		self.rhandle = [x.get_rect(center=self.rfill.midright) for x in self.handle]

	def event(self, event):
		posMouse = [x+y for x,y in zip(self.posMouse, pygame.mouse.get_pos())]
		pressMouse = pygame.mouse.get_pressed()
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.rect.collidepoint(posMouse):
				self.active = True
		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			self.active = False

	def update(self):
		if not self.active: return
		posMouse = [x+y for x,y in zip(self.posMouse, pygame.mouse.get_pos())]
		pos = posMouse[0]
		left = self.rtrack.x + self.rhandle[0].w//2
		right = self.rtrack.x + self.rtrack.w - self.rhandle[0].w//2
		if pos < left: pos = left
		elif pos > right: pos = right
		self.rhandle[0].centerx = self.rhandle[1].centerx = pos
		self.rfill.w = pos - self.rfill.x

	def draw(self, surface):
		posMouse = [x+y for x,y in zip(self.posMouse, pygame.mouse.get_pos())]
		pressMouse = pygame.mouse.get_pressed()
		self.update()
		surface.blit(self.track, self.rtrack)
		surface.blit(self.leftfill, self.rfill)
		pygame.draw.rect(surface, self.cfill, self.rfill, border_radius=self.rfill.h)
		if self.rhandle[0].collidepoint(posMouse) and not pressMouse[0]:
			surface.blit(self.handle[1], self.rhandle[1])
		else:
			surface.blit(self.handle[0], self.rhandle[0])

	@property
	def level(self):
		ratio = (self.rfill.w-self.rhandle[0].w//2)/(self.rtrack.w-self.rhandle[0].w//2*2)
		level = ratio*(self.range[1]-self.range[0])-self.range[0]
		return level
	@level.setter
	def level(self, level):
		ratio = (level-self.range[0])/(self.range[1]-self.range[0])
		self.rfill.w = ratio*(self.rtrack.w-self.rhandle[0].w//2*2)+self.rhandle[0].w//2
		self.rhandle[0].centerx = self.rhandle[1].centerx = self.rfill.x+self.rfill.w
	def pos_mouse(self, pos):
		self.posMouse = pos
	def is_active(self):
		return self.active

def renderCircle(color, radius, factor=2):
	s = pygame.Surface((radius*2*factor, radius*2*factor), pygame.SRCALPHA)
	pygame.draw.circle(s, color, (radius*factor, radius*factor), radius*factor)
	s = pygame.transform.smoothscale_by(s, 1/factor)
	s = maskFill(s, color)
	return s

def renderRect(color, size, radius=0, factor=2):
	s = pygame.Surface(size, pygame.SRCALPHA)
	pygame.draw.rect(s, color, (0, radius, size[0], size[1]-radius*2))
	pygame.draw.rect(s, color, (radius, 0, size[0]-radius*2, size[1]))
	circle = renderCircle(color, radius, factor)
	s.blit(circle, (0,0))
	s.blit(circle, (size[0]-radius*2, 0))
	s.blit(circle, (size[0]-radius*2, size[1]-radius*2))
	s.blit(circle, (0, size[1]-radius*2))
	return s

def blendColor(surface, color, rect=None, flags=pygame.BLEND_RGBA_MULT):
	surface = surface.copy()
	color = (color)
	surface.fill(color, rect, flags)
	return surface

def maskFill(surface, color, rect=None):
	surface = surface.copy()
	surface.fill((255,255,255,0), rect, pygame.BLEND_RGBA_MAX)
	surface.fill(color, rect, pygame.BLEND_RGBA_MULT)
	return surface

class Snow:
	def __init__(self, snow, pos, speed):
		self.snow = snow
		self.rect = self.snow.get_rect(center = pos)
		self.speed = speed
		self.timefall = Timer(10)
		self.timewind = Timer(30)
		self.speedwind = random.choice([-1,0,1,1])

	def update(self):
		if self.timewind.update():
			self.rect.x += self.speedwind
		if self.timefall.update():
			self.rect.y += self.speed

	def draw(self, surface):
		surface.blit(self.snow, self.rect)
	@property
	def pos(self):
		return self.rect.center

class Snowfall:
	def __init__(self, surface):
		self.surface = surface
		self.rect = self.surface.get_rect()
		self.snow = [pygame.image.load(BytesIO(snow)).convert_alpha() for snow in data.media["snow"]]
		self.listSnow = []
		self.timecreate = Timer(150)

	def createSnow(self):
		speed = random.choice([1,1,1,2,2,3,3,6])
		pos = (random.randint(0, self.surface.get_width()), 0)
		height = random.randint(2, 19)
		snow = random.choice(self.snow)
		snow = pygame.transform.smoothscale_by(snow, height/snow.get_height())
		self.listSnow.append(Snow(snow, pos, speed))
		
	def update(self):
		if self.timecreate.update():
			self.createSnow()
		for snow in self.listSnow.copy():
			if not self.rect.collidepoint(snow.pos):
				self.listSnow.remove(snow)
		for snow in self.listSnow:
			snow.update()

	def draw(self):
		for snow in self.listSnow:
			snow.draw(self.surface)

if __name__ == "__main__":
	game = Game()
	game.loop()