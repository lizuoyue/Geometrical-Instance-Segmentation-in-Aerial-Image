class Config(object):
	def __init__(self):
		# 
		self.AREA_SIZE      = [224, 224]
		self.AREA_SIZE_2    = [int(item /  2) for item in self.AREA_SIZE]
		self.AREA_SIZE_4    = [int(item /  4) for item in self.AREA_SIZE]
		self.AREA_SIZE_8    = [int(item /  8) for item in self.AREA_SIZE]
		self.AREA_SIZE_16   = [int(item / 16) for item in self.AREA_SIZE]
		self.AREA_SIZE_32   = [int(item / 32) for item in self.AREA_SIZE]

		#
		self.BEAM_WIDTH = 4
		self.BEAM_WIDTH_2 = int(self.BEAM_WIDTH / 2)

		self.TABLEAU20 = [
			(174, 199, 232), (255, 187, 120), (152, 223, 138), (255, 152, 150), (197, 176, 213),
			(196, 156, 148), (247, 182, 210), (199, 199, 199), (219, 219, 141), (158, 218, 229),
		]
		# Blu Org Grn Red Prp
		# Brn Pnk Gry Ylw Aoi
		self.TABLEAU20_DEEP = [
			( 31, 119, 180), (255, 127,  14), ( 44, 160,  44), (214,  39,  40), (148, 103, 189),
			(140,  86,  75), (227, 119, 194), (127, 127, 127), (188, 189,  34), ( 23, 190, 207),
		]

		# Learning parameters
		self.NUM_ITER = 1200001
		self.MAX_NUM_VERTICES = 20
		self.LEARNING_RATE = 1e-5
		self.LSTM_OUT_CHANNEL = [64, 32, 16, 8]
		self.V_OUT_RES = tuple(self.AREA_SIZE_8)
		self.AREA_TRAIN_BATCH = 4
		self.AREA_VALID_BATCH = 6
		self.AREA_TEST_BATCH = 8

		self.TRAIN_NUM_PATH = 8
		self.VALID_NUM_PATH = 12

		self.PATH = {
			'roadtracer-dalabgpu': {
				'img-train': '/local/home/zoli/data/roadtracer/train_images',
				'img-val'  : '/local/home/zoli/data/roadtracer/test_images',
				'img-test' : '/local/home/zoli/data/roadtracer/test_images',
				'ann-train': '/local/home/zoli/data/roadtracer/roadtracer_train.json',
				'ann-val'  : '/local/home/zoli/data/roadtracer/roadtracer_test.json',
				'ann-test' : '/local/home/zoli/data/roadtracer/roadtracer_test.json',
				'bias'     : [100.28884016, 101.06444319, 89.79566705]
			},
			'roadtracer-big': {
				'img-train': '/local/home/zoli/data/roadtracer-big/train_images',
				'img-val'  : '/local/home/zoli/data/roadtracer-big/test_images',
				'img-test' : '/local/home/zoli/data/roadtracer-big/test_images',
				'ann-train': '/local/home/zoli/data/roadtracer-big/roadtracer_train.json',
				'ann-val'  : '/local/home/zoli/data/roadtracer-big/roadtracer_test.json',
				'ann-test' : '/local/home/zoli/data/roadtracer-big/roadtracer_test.json',
				'bias'     : [100.28884016, 101.06444319, 89.79566705]
			},
			'roadtracer-leonhard': {
				'img-train': '/cluster/scratch/zoli/roadtracer/train_images',
				'img-val'  : '/cluster/scratch/zoli/roadtracer/test_images',
				'img-test' : '/cluster/scratch/zoli/roadtracer/test_images',
				'ann-train': '/cluster/scratch/zoli/roadtracer/roadtracer_train.json',
				'ann-val'  : '/cluster/scratch/zoli/roadtracer/roadtracer_test.json',
				'ann-test' : '/cluster/scratch/zoli/roadtracer/roadtracer_test.json',
				'bias'     : [100.28884016, 101.06444319, 89.79566705]
			},
			'Chicago': {
				'img-train': '/local/home/zoli/data/Chicago/ChicagoPatch',
				'img-val'  : '/local/home/zoli/data/Chicago/ChicagoPatch',
				'img-test' : '/local/home/zoli/data/Chicago/ChicagoPatch',
				'ann-train': '/local/home/zoli/data/Chicago/ChicagoRoadTrain.json',
				'ann-val'  : '/local/home/zoli/data/Chicago/ChicagoRoadVal.json',
				'ann-test' : '/local/home/zoli/data/Chicago/ChicagoRoadTest.json',
				'bias'     : [84.60222819, 80.07855799, 70.79262454]
			},
			'Sunnyvale': {
				'img-train': '/local/home/zoli/data/Sunnyvale/SunnyvalePatch',
				'img-val'  : '/local/home/zoli/data/Sunnyvale/SunnyvalePatch',
				'img-test' : '/local/home/zoli/data/Sunnyvale/SunnyvalePatch',
				'ann-train': '/local/home/zoli/data/Sunnyvale/SunnyvaleRoadTrain.json',
				'ann-val'  : '/local/home/zoli/data/Sunnyvale/SunnyvaleRoadVal.json',
				'ann-test' : '/local/home/zoli/data/Sunnyvale/SunnyvaleRoadTest.json',
				'bias'     : [107.52448122, 106.82606879, 98.10730461]
			},
			'Boston': {
				'img-train': '/local/home/zoli/data/Boston/BostonPatch',
				'img-val'  : '/local/home/zoli/data/Boston/BostonPatch',
				'img-test' : '/local/home/zoli/data/Boston/BostonPatch',
				'ann-train': '/local/home/zoli/data/Boston/BostonRoadTrain.json',
				'ann-val'  : '/local/home/zoli/data/Boston/BostonRoadVal.json',
				'ann-test' : '/local/home/zoli/data/Boston/BostonRoadTest.json',
				'bias'     : [76.86692809, 75.58776253, 67.1285512]
			},
			'Chicago-leonhard': {
				'img-train': '/cluster/scratch/zoli/Chicago/ChicagoPatch',
				'img-val'  : '/cluster/scratch/zoli/Chicago/ChicagoPatch',
				'img-test' : '/cluster/scratch/zoli/Chicago/ChicagoPatch',
				'ann-train': '/cluster/scratch/zoli/Chicago/ChicagoRoadTrain.json',
				'ann-val'  : '/cluster/scratch/zoli/Chicago/ChicagoRoadVal.json',
				'ann-test' : '/cluster/scratch/zoli/Chicago/ChicagoRoadTest.json',
				'bias'     : [84.60222819, 80.07855799, 70.79262454]
			},
			'Sunnyvale-leonhard': {
				'img-train': '/cluster/scratch/zoli/Sunnyvale/SunnyvalePatch',
				'img-val'  : '/cluster/scratch/zoli/Sunnyvale/SunnyvalePatch',
				'img-test' : '/cluster/scratch/zoli/Sunnyvale/SunnyvalePatch',
				'ann-train': '/cluster/scratch/zoli/Sunnyvale/SunnyvaleRoadTrain.json',
				'ann-val'  : '/cluster/scratch/zoli/Sunnyvale/SunnyvaleRoadVal.json',
				'ann-test' : '/cluster/scratch/zoli/Sunnyvale/SunnyvaleRoadTest.json',
				'bias'     : [107.52448122, 106.82606879, 98.10730461]
			},
			'Boston-leonhard': {
				'img-train': '/cluster/scratch/zoli/Boston/BostonPatch',
				'img-val'  : '/cluster/scratch/zoli/Boston/BostonPatch',
				'img-test' : '/cluster/scratch/zoli/Boston/BostonPatch',
				'ann-train': '/cluster/scratch/zoli/Boston/BostonRoadTrain.json',
				'ann-val'  : '/cluster/scratch/zoli/Boston/BostonRoadVal.json',
				'ann-test' : '/cluster/scratch/zoli/Boston/BostonRoadTest.json',
				'bias'     : [76.86692809, 75.58776253, 67.1285512]
			}
		}