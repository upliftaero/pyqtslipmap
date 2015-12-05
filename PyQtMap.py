from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtOpenGL import QGLWidget
import math
from OpenGL.GL import *
from OpenGL.GLUT import *
import OpenGL.arrays.vbo as glvbo
import numpy
from PIL import Image
import string
from geo import *
from os.path import expanduser

# TILE REFERENCES
# see http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
# see http://wiki.openstreetmap.org/wiki/Zoom_levels
# http://go2log.com/2011/09/26/fetching-tiles-for-offline-map/

# OPENGL REFERENCES
# http://stackoverflow.com/questions/5907613/render-a-textured-rectangle-with-pyopengl

# Coordinate systems:
# Screen pixels
# Lat lon
# Tiles
# Distance (m)


class TileException(Exception):
	'''tile error class'''
	def __init__(self, msg):
		Exception.__init__(self, msg)

TILE_SERVICES = {
	# thanks to http://go2log.com/2011/09/26/fetching-tiles-for-offline-map/
	# for the URL mapping info
	"GoogleSat"      : "https://khm${GOOG_DIGIT}.google.com/kh/v=157&hl=pt-PT&x=${X}&y=${Y}&z=${ZOOM}&s=${GALILEO}",
	"GoogleMap"      : "https://mt${GOOG_DIGIT}.google.com/vt/lyrs=m@132&hl=pt-PT&x=${X}&y=${Y}&z=${ZOOM}&s=${GALILEO}",
	"GoogleTer"      : "https://mt${GOOG_DIGIT}.google.com/vt/v=t@132,r@249&hl=pt-PT&x=${X}&y=${Y}&z=${ZOOM}&s=${GALILEO}",
	"GoogleChina"    : "http://mt${GOOG_DIGIT}.google.cn/vt/lyrs=m@121&hl=en&gl=cn&x=${X}&y=${Y}&z=${ZOOM}&s=${GALILEO}",
	"MicrosoftBrMap" : "http://imakm${MS_DIGITBR}.maplink3.com.br/maps.ashx?v=${QUAD}|t&call=2.2.4",
	"MicrosoftHyb"   : "http://ecn.t${MS_DIGIT}.tiles.virtualearth.net/tiles/h${QUAD}.png?g=441&mkt=en-us&n=z",
	"MicrosoftSat"   : "http://ecn.t${MS_DIGIT}.tiles.virtualearth.net/tiles/a${QUAD}.png?g=441&mkt=en-us&n=z",
	"MicrosoftMap"   : "http://ecn.t${MS_DIGIT}.tiles.virtualearth.net/tiles/r${QUAD}.png?g=441&mkt=en-us&n=z",
	"MicrosoftTer"   : "http://ecn.t${MS_DIGIT}.tiles.virtualearth.net/tiles/r${QUAD}.png?g=441&mkt=en-us&shading=hill&n=z",
        "OviSat"         : "http://maptile.maps.svc.ovi.com/maptiler/v2/maptile/newest/satellite.day/${Z}/${X}/${Y}/256/png8",
        "OviHybrid"      : "http://maptile.maps.svc.ovi.com/maptiler/v2/maptile/newest/hybrid.day/${Z}/${X}/${Y}/256/png8",
	"OpenStreetMap"  : "http://tile.openstreetmap.org/${ZOOM}/${X}/${Y}.png",
	"OSMARender"     : "http://tah.openstreetmap.org/Tiles/tile/${ZOOM}/${X}/${Y}.png",
	"OpenAerialMap"  : "http://tile.openaerialmap.org/tiles/?v=mgm&layer=openaerialmap-900913&x=${X}&y=${Y}&zoom=${OAM_ZOOM}",
	"OpenCycleMap"   : "http://andy.sandbox.cloudmade.com/tiles/cycle/${ZOOM}/${X}/${Y}.png",
	"StatKartTopo2" : "http://opencache.statkart.no/gatekeeper/gk/gk.open_gmaps?layers=topo2&zoom=${ZOOM}&x=${X}&y=${Y}"

	}

# these are the md5sums of "unavailable" tiles
BLANK_TILES = set(["d16657bbee25d7f15c583f5c5bf23f50",
                   "c0e76e6e90ff881da047c15dbea380c7",
		   "d41d8cd98f00b204e9800998ecf8427e"])

# all tiles are 256x256
TILES_WIDTH = 256
TILES_HEIGHT = 256

cache_path = expanduser("~") + os.sep + "tiles"

class QSlipMap(QGLWidget):
    def __init__(self, parent):
        super(QSlipMap, self).__init__(parent)

        # Uncomment this to fire mouseMoveEvents every time the mouse is moved
        #self.setMouseTracking(True)

        self.coordsLatLon = QLatLon()
        self.coordsTile = QPoint()
        self.coordsRect = QRectF()
        self.zoom = 3
        self.service = "MicrosoftHyb"

        self.textures_loading = None
        self.textures_tiles = {}

        tl = TileLoader()
        tl.fetch_tiles(self.service, 12, 3, 4, 5, 5)

        self.plane1 = QLatLon(37.424028, -122.177804)
        self.plane2 = QLatLon(37.421188, -122.175255)


    def mousePressEvent(self, evt):
        click_latlon = self.latlon_from_screen(evt.x(), evt.y())
        print(click_latlon)

    def mouseMoveEvent(self, evt):
        #print(' Mouse move: ' + str(self.latlon_from_screen(evt.x(), evt.y())))
        return

    def setCenterCoordinate(self, coord):
        self.coordsLatLon = coord
        self.coordsTile = latlon_to_tile(self.coordsLatLon, self.zoom)
        self.update()

    def setZoom(self, zoom):
        self.zoom = zoom
        print('lat:' + str(self.coordsLatLon.lat))
        self.meters_per_pixel = meters_per_pixel(self.coordsLatLon.lat, zoom)
        print(self.meters_per_pixel)
        self.update()

    def latlon_from_screen(self, screenx, screeny):
        '''
        Get the lat-lon of the given scren coordinates
        '''
        centerx = self.width/2
        centery = self.height/2
        dx = (screenx - centerx) * self.meters_per_pixel
        dy = (screeny - centery) * self.meters_per_pixel
        return gps_offset(self.coordsLatLon.lat, self.coordsLatLon.lon, dx, -dy)

    def screen_from_latlon(self, coord):
        '''
        Get the screen coordinates of the given lat-lon
        '''
        centerx = self.width/2
        centery = self.height/2
        dist = gps_distance(self.coordsLatLon.lat, self.coordsLatLon.lon, coord.lat, coord.lon)
        delta = gps_relxy(self.coordsLatLon.lat, self.coordsLatLon.lon, coord.lat, coord.lon)
        screenx = delta.x() / self.meters_per_pixel + centerx
        screeny = delta.y() / self.meters_per_pixel + centery
        return QPointF(screenx, screeny)


    def initializeGL(self):
        glClearColor(0,0,0,0)
        glMatrixMode(GL_PROJECTION)
        self.tex = self.loadTexture('2.png')
        self.planetex = self.loadTexture('blueplane.png')
        self.textures_loading = self.loadTexture('loading.png')

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.width, self.height, 0.0, 0.0, 1.0)
        glMatrixMode (GL_MODELVIEW)
        glLoadIdentity()
        self.renderMap()
        self.swapBuffers()

    def renderMap(self):
        # The boundaries of the drawing area in tile coordinates. (x1,y1) is the top-left tile number.
        x1 = self.coordsTile.x() - self.width_tiles/2
        x2 = self.coordsTile.x() + self.width_tiles/2
        y1 = self.coordsTile.y() - self.height_tiles/2
        y2 = self.coordsTile.y() + self.height_tiles/2

        # The scren coordinates where the top-left tile starts. These will be negative numbers,
        # becuase we always draw a band of tiles around the visible area.
        x1_screen = (self.width/2 - 128) - (self.width_tiles/2 * 256)
        y1_screen = (self.height/2 -128) - (self.height_tiles/2 * 256)


        # This generates a dictionary of tile keys that we need to load
        tilekeys = {}
        for x in range(0, self.width_tiles):
            for y in range(0, self.height_tiles):
                # Screen coordinates for the tile we are about to draw
                sx = x1_screen + x*256
                sy = y1_screen + y*256

                # TODO load tiles here
                self.drawTexture(self.textures_loading, sx, sy, 256, 256)
                #tilekeys[x,y] = tilekey(self.service, self.zoom, x1 + x, y1 + y)
        print(tilekeys)

        #self.drawTexture(self.tex, 5, 5, 256, 256)



        self.plane1coords = self.screen_from_latlon(self.plane1)
        #self.plane2coords = self.screen_from_latlon(self.plane2.y(), self.plane2.x())
        #print(self.plane1coords, self.plane2coords)
        self.drawTexture(self.planetex, self.plane1coords.x(), self.plane1coords.y(), 64, 64)
        #self.drawTexture(self.planetex, self.plane2coords.x(), self.plane2coords.y(), 64, 64)


    def resizeGL(self, width, height):
        self.width = width
        self.height = height
        self.height_tiles = self.height/256 + 2
        self.width_tiles = self.width/256 + 2
        glViewport(0, 0, width, height)

    def draw_rect(self, x, y, width, height):
        glBegin(GL_QUADS)  # start drawing a rectangle
        glVertex2f(x, y)  # bottom left point
        glVertex2f(x + width, y)  # bottom right point
        glVertex2f(x + width, y + height)  # top right point
        glVertex2f(x, y + height)  # top left point
        glEnd()

    def draw_border(self, x, y, width, height):
        glBegin(GL_LINES)

        glVertex2d(x, y)
        glVertex2d(x + width, y)

        glVertex2d(x + width, y)
        glVertex2d(x + width, y + height)

        glVertex2d(x + width, y + height)
        glVertex2d(x, y + height)

        glVertex2d(x, y + height)
        glVertex2d(x, y)

        glEnd()

    def loadTexture(self, name):

        img = Image.open(name)
        try:
            ix, iy, image = img.size[0], img.size[1], img.convert("RGBA").tostring("raw", "RGBA")
        except SystemError:
            ix, iy, image = img.size[0], img.size[1], img.convert("RGBA").tostring("raw", "RGBX")
        id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        return id

    def drawTexture(self, texture_id, x, y, width, height):
        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glBegin(GL_QUADS)  # start drawing a rectangle
        glTexCoord2f(0.0, 0.0)
        glVertex2f(x, y)  # bottom left point
        glTexCoord2f(1.0, 0.0)
        glVertex2f(x + width, y)  # bottom right point
        glTexCoord2f(1.0, 1.0)
        glVertex2f(x + width, y + height)  # top right point
        glTexCoord2f(0.0, 1.0)
        glVertex2f(x, y + height)  # top left point
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def tilepath(self, service, x, y, zoom):
        return cache_path + os.sep + service + os.sep + str(zoom)

    def tilefile(self, service, x, y, zoom):
        return cache_path + os.sep + service + os.sep + str(zoom) + os.sep + str(x) + '_' + str(y) + '.png'



def latlon_to_tile(coords, zoom):
    lon_deg = coords.lon
    lat_deg = coords.lat

    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return QPoint(xtile, ytile)

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return QLatLon(lat_deg, lon_deg)


class TileServiceInfo:
	'''a lookup object for the URL templates'''
	def __init__(self, x, y, zoom):
		self.X = x
		self.Y = y
		self.Z = zoom
		quadcode = ''
		for i in range(zoom - 1, -1, -1):
			quadcode += str((((((y >> i) & 1) << 1) + ((x >> i) & 1))))
		self.ZOOM = zoom
		self.QUAD = quadcode
		self.OAM_ZOOM = 17 - zoom
		self.GOOG_DIGIT = (x + y) & 3
		self.MS_DIGITBR = (((y & 1) << 1) + (x & 1)) + 1
		self.MS_DIGIT = (((y & 3) << 1) + (x & 1))
		self.Y_DIGIT = (x + y + zoom) % 3 + 1
		self.GALILEO = "Galileo"[0:(3 * x + y) & 7]

	def __getitem__(self, a):
		return str(getattr(self, a))


class Tile:
    def __init__(self, service, x, y, zoom):
        self.service = service
        self.x = x
        self.y = y
        self.zoom = zoom

    def get_url(self):
        '''return URL for a tile'''
        if self.service not in TILE_SERVICES:
            raise TileException('unknown tile service %s' % self.service)
		url = string.Template(TILE_SERVICES[self.service])
		tile_info = TileServiceInfo(self.x, self.y, self.zoom)
		return url.substitute(tile_info)

    def tilekey(self):
        return self.service + '_' + str(self.zoom) + '_' + str(self.x) + '_' + str(self.y)

    def tilepath(self):
        return cache_path + os.sep + self.service + os.sep + str(self.zoom)

    def tilefile(self):
        return cache_path + os.sep + self.service + os.sep + str(self.zoom) + os.sep + str(self.x) + '_' + str(self.y) + '.png'


class QMapDownloaderThread(QThread):

    def __init__(self):
        super(QMapDownloaderThread, self).__init__()
        self.tiles_to_download = {}
        self.command_exit = False
        return

    def add_tile(self, service, zoom, x, y):
        self.tiles_to_download.append(Tile(service, x, y, zoom))
        return

    def run(self):
        while self.command_exit is False:
            if len(self.tiles_to_download) > 0:
                turl = self.tiles_to_download[0].get_url()
                tfile = self.tiles_to_download[0].tilefile()

                time.sleep(self.tile_delay)

			keys = self._download_pending.keys()[:]

			# work out which one to download next, choosing by request_time
			tile_info = self._download_pending[keys[0]]
			for key in keys:
				if self._download_pending[key].request_time > tile_info.request_time:
					tile_info = self._download_pending[key]

			url = tile_info.url(self.service)
			path = self.tile_to_path(tile_info)
			key = tile_info.key()

			try:
				if self.debug:
					print("Downloading %s [%u left]" % (url, len(keys)))
                                req = urllib2.Request(url)
                                if url.find('google') != -1:
                                        req.add_header('Referer', 'https://maps.google.com/')
				resp = urllib2.urlopen(req)
				headers = resp.info()
			except urllib2.URLError as e:
				#print('Error loading %s' % url)
                                if not key in self._tile_cache:
                                        self._tile_cache[key] = self._unavailable
				self._download_pending.pop(key)
				if self.debug:
					print("Failed %s: %s" % (url, str(e)))
				continue
			if 'content-type' not in headers or headers['content-type'].find('image') == -1:
                                if not key in self._tile_cache:
                                        self._tile_cache[key] = self._unavailable
				self._download_pending.pop(key)
				if self.debug:
					print("non-image response %s" % url)
				continue
			else:
				img = resp.read()

			# see if its a blank/unavailable tile
			md5 = hashlib.md5(img).hexdigest()
			if md5 in BLANK_TILES:
				if self.debug:
					print("blank tile %s" % url)
                                if not key in self._tile_cache:
                                        self._tile_cache[key] = self._unavailable
				self._download_pending.pop(key)
				continue

			mp_util.mkdir_p(os.path.dirname(path))
			h = open(path+'.tmp','wb')
			h.write(img)
			h.close()
                        try:
                                os.unlink(path)
                        except Exception:
                                pass
                        os.rename(path+'.tmp', path)
			self._download_pending.pop(key)

        return


def tilekey(service, x, y, zoom):
    return service + '_' + str(zoom) + '_' + str(x) + '_' + str(y)
