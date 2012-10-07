# Unit test for testing webapp WITHOUT uploading a file every time

import sys, os, unittest, imp,json
#from ipdb import set_trace

sys.path.append('../main/lib') # to find the classes to test
sys.path.append('../main/wsgi')

import helper, mediafactory, configuration, gtr
from webtest import TestApp



class TestExistingWSGI(unittest.TestCase):

    def setUp(self):
        self.app = TestApp(gtr.application)
        self.uuid = configuration.getSampleUUID()

    #@unittest.skip("skipping getUUIDs test")    
    def test_geotag(self):
        (lon,lat) = (-3.1901, 54.9545)
        d = 0.01
        # 1) Get geotag
        rawres = self.app.get("/geotag/%s"%self.uuid, { "lon": lon, "lat" : lat } )
        res2 = rawres.json
        self.assertEqual ( res2["error"], 0)
        # 2) Get bbox
        rawres = self.app.get("/getUUIDs", { "bbox" : "%s,%s,%s,%s" % (lon-d,lat-d, lon+d, lat+d) } )
        res2 = rawres.json
        print res2
        #self.assertEqual(res2["uuids"],"sample_uuid")
        # 2) Get keys
        rawres = self.app.get("/getUUIDs", { "key":"water"} )
        res2 = rawres.json
        self.assertEqual(res2["tagger_uuids"],"sample_uuid")
        # 3) geotag using placename
        rawres = self.app.get("/geotag/%s"%self.uuid, { "placename": 'edinburgh' } )
        res2 = rawres.json
        print res2
        self.assertEqual ( res2["error"], 0)


    @unittest.skip("skipping custom/keyword test")
    def test_custom(self):
        """
        1) Set custom tag
        2) Set keyword
        3) Get all keywords
        4) find media by keyword
        """
        uuid = self.uuid
        # 1a) save custom tag
        rawres = self.app.post("/saveMetadata/%s"%uuid, {'group':'Custom','metadata':'{"test":"value"}'})
        res = rawres.json
        self.assertEqual ( res["error"], 0)
        # 1b) verify metadata
        res = self.app.get("/loadMetadata/%s"%uuid,{'group':'Custom'}).json
        self.assertEqual ( res["test"], "value")
        # 2) Set keyword (ie. edit "tags" custom tag)
        res = self.app.get("/addKeyword/%s"%uuid, { 'key':'water'}).json
        print `res`
        self.assertEqual(res["error"], 0)        
        res = self.app.get("/addKeyword/%s"%uuid, { 'key': 'big town'}).json
        self.assertEqual(res["error"], 0)        
        # 3) Get all keywords
        res = self.app.get("/getKeywords/%s"%uuid).json
        self.assertTrue(res.has_key("keywords"))

    #@unittest.skip("skipping license test")
    def test_licence(self):
        """
        1) Set CC license
        1b) getlicense 
        2) Set arbitrary licence
        2b) Get license
        3) export XMP
        """
        uuid = self.uuid
        # 1) set CC license
        # note: "license" becomes "License" (exiftool peculiarity followed by custom tags for consistency)
        res = self.app.get("/setLicense/%s"%uuid,{'license':'CC-SA'}).json
        self.assertEqual ( res["error"], 0)
        # test result with loadmetadata
        res = self.app.get("/loadMetadata/%s"%uuid,{'group':'XMP-cc'}).json
        self.assertEqual(res["License"], configuration.getCCMap()["CC-SA"])
        # test result with getlicense
        res = self.app.get("/getLicense/%s"%uuid).json
        self.assertEqual(res["license"], configuration.getCCMap()["CC-SA"])        
        # 2) Set arbitrary license
        res = self.app.get("/setLicense/%s"%uuid,{'license':'Arbitrary license'}).json
        self.assertEqual ( res["error"], 0)
        # test result with loadmetadata
        res = self.app.get("/loadMetadata/%s"%uuid,{'group':'Custom'}).json
        self.assertEqual(res["License"], "Arbitrary license")
        # test result with getlicense after deleting conflicting licenses
        res = self.app.post("/saveMetadata/%s"%uuid,{'metadata':'{"License":""}'}).json
        self.assertEqual ( res["error"], 0)        
        res = self.app.get("/getLicense/%s"%uuid).json
        self.assertEqual(res["license"], "Arbitrary license")        
        # 3) Export XMP
        res = self.app.get("/export/%s"%uuid).body
        #print res
                
if __name__ == '__main__':
    unittest.main()
