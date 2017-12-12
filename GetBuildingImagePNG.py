import io, os, sys
import numpy as np
import requests, math
from PIL import Image, ImageDraw
ut = __import__('Utility')
bli = __import__('GetBuildingListOSM')

class BuildingImageDownloader(object):

	def __init__(self, google_keys_filename, city_name):
		f = open(google_keys_filename, 'r')
		self.keys = [item.strip() for item in f.readlines()]
		f.close()
		self.city_name = city_name

	def norm(self, p):
		l = math.sqrt(p[0] ** 2 + p[1] ** 2)
		return (p[0] / l, p[1] / l)

	def centerRight(self, p1, p2, l):
		direction = (p1[1] - p2[1], p2[0] - p1[0])
		direction = self.norm(direction)
		x = math.floor((p1[0] + p2[0]) / 2 + l * direction[0])
		y = math.floor((p1[1] + p2[1]) / 2 + l * direction[1])
		return (x, y)

	def saveImagePolygon(self, img, polygon):
		# Save images
		img = Image.fromarray(img)
		mask = Image.new('RGBA', img.size, color = (255, 255, 255, 0))
		draw = ImageDraw.Draw(mask)
		draw.polygon(polygon, fill = (255, 0, 0, 128), outline = (255, 0, 0, 128))
		merge = Image.alpha_composite(img, mask)
		img.save('../%s/%d/img.png' % (self.city_name, building_id))
		# mask.save('../%s/%d/mask.png' % (self.city_name, building_id))
		# merge.save('../%s/%d/merge.png' % (self.city_name, building_id))

		# Decide the order of vertices
		inner_count = 0
		for i in range(len(polygon)):
			x, y = self.centerRight(polygon[i - 1], polygon[i], 5)
			try:
				inner_count += (np.sum(mask[y, x, 1: 3]) > 1.0) # <- The pixel is not red
			except:
				inner_count += 1
		if inner_count / len(polygon) < 0.5:
			polygon.reverse()

		# Save as text file to save storage
		f = open('../%s/%d/polygon.txt' % (self.city_name, building_id), 'w')
		for point in polygon:
			f.write('%d %d\n' % point)
		f.close()

		# Return
		return

	def getBuildingAerialImage(self, idx, building, scale = 2, size = (224, 224), building_id = None):
		# Check inputs
		pad = 100
		pad_rate = 0.8
		assert(scale == 1 or scale == 2)
		if scale == 2:
			assert(size[0] % 2 == 0)
			assert(size[1] % 2 == 0)
			size_g = (int(size[0] / 2) + pad, int(size[1] / 2) + pad)
		else:
			size_g = (size[0] + pad * 2, size[1] + pad * 2)
		assert(building_id != None)

		# Create new folder
		if not os.path.exists('../%s/%d' % (self.city_name, building_id)):
			os.makedirs('../%s/%d' % (self.city_name, building_id))

		# Decide the tight bounding box
		min_lon, max_lon = 200.0, -200.0
		min_lat, max_lat = 100.0, -100.0
		for lon, lat in building:
			min_lon = min(lon, min_lon)
			min_lat = min(lat, min_lat)
			max_lon = max(lon, max_lon)
			max_lat = max(lat, max_lat)
		c_lon = (min_lon + max_lon) / 2.0
		c_lat = (min_lat + max_lat) / 2.0

		# Decide the zoom level
		zoom = 20
		left, up = ut.lonLatToPixel(min_lon, max_lat, zoom + scale - 1)
		right, down = ut.lonLatToPixel(max_lon, min_lat, zoom + scale - 1)
		while right - left > math.floor(size[0] * pad_rate) or down - up > math.floor(size[1] * pad_rate): # <- Decide the padding
			zoom -= 1
			assert(zoom > 0)
			left, up = ut.lonLatToPixel(min_lon, max_lat, zoom + scale - 1)
			right, down = ut.lonLatToPixel(max_lon, min_lat, zoom + scale - 1)
		print('%d, %d, Final zoom = %d.' % (idx, building_id, zoom))
		
		# Get image from Google Map API
		while True:
			try:
				data = requests.get(
					'https://maps.googleapis.com/maps/api/staticmap?' 			+ \
					'maptype=%s&' 			% 'satellite' 						+ \
					'center=%.7lf,%.7lf&' 	% (c_lat, c_lon) 					+ \
					'zoom=%d&' 				% zoom 								+ \
					'size=%dx%d&' 			% size_g						 	+ \
					'scale=%d&' 			% scale 							+ \
					'format=%s&' 			% 'png32' 							+ \
					'key=%s' 				% self.keys[idx % len(self.keys)] 	  \
				).content
				img = np.array(Image.open(io.BytesIO(data)))
				break
			except:
				print('Try again to get the image.')
				pass

		# Image large
		img = img[pad: img.shape[0] - pad, pad: img.shape[1] - pad, ...]

		# Compute polygon's vertices
		bbox = ut.BoundingBox(c_lon, c_lat, zoom, scale, size)
		polygon = [] # <- polygon: (col, row)
		for lon, lat in building:
			px, py = bbox.lonLatToRelativePixel(lon, lat)
			if not polygon or (px, py) != polygon[-1]:
				polygon.append((px, py))
		if polygon[-1] == polygon[0]:
			polygon.pop()

		# Save and return
		self.saveImagePolygon(img, polygon)
		return

if __name__ == '__main__':
	assert(len(sys.argv) == 4)
	city_name = sys.argv[1]
	idx_beg = int(sys.argv[2])
	idx_end = int(sys.argv[3])
	objCons = bli.BuildingListConstructor(range_vertices = (4, 15), filename = './BuildingList-%s.npy' % city_name)
	objDown = BuildingImageDownloader('./GoogleMapAPIKey.txt', city_name)
	id_list = [k for k in objCons.building]
	id_list.sort()
	for i, building_id in enumerate(id_list):
		if i < idx_beg or i >= idx_end:
			continue
		objDown.getBuildingAerialImage(i, objCons.building[building_id], building_id = building_id)

