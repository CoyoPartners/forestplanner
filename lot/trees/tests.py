import os
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from json import loads, dumps
from madrona.features import *
from madrona.features.models import Feature, PointFeature, LineFeature, PolygonFeature, FeatureCollection
from madrona.features.forms import FeatureForm
from madrona.common.utils import kml_errors, enable_sharing
from madrona.raster_stats.models import RasterDataset
from trees.models import Stand, Strata, ForestProperty, County, FVSVariant, Scenario
from trees.utils import StandImporter

cntr = GEOSGeometry('SRID=3857;POINT(-13842474.0 5280123.1)')
g1 = cntr.buffer(75)
g1.transform(settings.GEOMETRY_DB_SRID)

single_p1 = g1.buffer(1000)
p1 = MultiPolygon(single_p1)

def import_rasters():
    d = os.path.dirname(__file__)
    rast_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
        'testdata'))
    # Here we'll need to create dummy rasterdatasets for everything 
    # in the IMPUTE_RASTERS setting
    elev = RasterDataset.objects.create(name="elevation",
            filepath=os.path.join(rast_path,'elevation.tif'), type='continuous')
    aspect = RasterDataset.objects.create(name="aspect",
            filepath=os.path.join(rast_path,'aspect.tif'), type='continuous')
    cos_aspect = RasterDataset.objects.create(name="cos_aspect",
            filepath=os.path.join(rast_path,'cos_aspect.tif'), type='continuous')
    sin_aspect = RasterDataset.objects.create(name="sin_aspect",
            filepath=os.path.join(rast_path,'sin_aspect.tif'), type='continuous')
    slope = RasterDataset.objects.create(name="slope",
            filepath=os.path.join(rast_path,'slope.tif'), type='continuous')

class StandTest(TestCase):
    ''' 
    Basic tests for adding stands
    '''

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_add_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        # geometry_final will be set with manipulator
        stand1.save()

    def test_delete_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        stand1.save()
        stand2.save()
        self.assertEqual(len(Stand.objects.all()), 2)
        Stand.objects.filter(name="My Stand2").delete()
        self.assertEqual(len(Stand.objects.all()), 1)

class ForestPropertyTest(TestCase):
    '''
    Basic tests for adding/removing stands from a property
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()

    def test_create_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

    def test_property_bbox(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()
        self.assertEqual(prop1.bbox, p1.extent)

    def test_add_property_to_stand(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

        self.stand1.add_to_collection(prop1)
        self.assertEqual(self.stand1.collection, prop1)
        self.assertTrue(self.stand1 in prop1.feature_set())

        self.stand1.remove_from_collection()
        self.assertEqual(self.stand1.collection, None)
        self.assertTrue(self.stand1 not in prop1.feature_set())

    def test_add_stand_to_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

        prop1.add(self.stand1)
        self.assertEqual(self.stand1.collection, prop1)
        self.assertTrue(self.stand1 in prop1.feature_set())

        prop1.remove(self.stand1)
        self.assertEqual(self.stand1.collection, None)
        self.assertTrue(self.stand1 not in prop1.feature_set())

    def test_add_property_to_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop2 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()
        prop2.save()
        # This `prop1.add(prop2)` should fail
        self.assertRaises(AssertionError, prop1.add, prop2)


class RESTTest(TestCase):
    '''
    Basic tests of the REST API 
    A bit of a dup of the features tests but more concise and specific
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.options = Stand.get_options()
        self.create_url = self.options.get_create_form()
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand1_form_url = self.options.get_update_form(self.stand1.pk)
        self.stand1_url = self.stand1.get_absolute_url()
        enable_sharing()

    def test_submit_not_authenticated(self):
        response = self.client.post(self.create_url, 
            {'name': "My Test", 'user': 1})
        self.assertEqual(response.status_code, 401)

    def test_submit_valid_form(self):
        old_count = Stand.objects.count()
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.create_url, {'name': 'test', 'geometry_orig': g1.wkt, })
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(old_count < Stand.objects.count())
        inst = Stand.objects.get(name='test')
        self.assertTrue(
            response._get_content().find(inst.get_absolute_url()) > -1)

    def test_get_form(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.get(self.stand1_form_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.find('My Stand'), -1)

    def test_post(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.stand1_url, {
            'name': 'My New Name', 
            'geometry_orig': self.stand1.geometry_orig.wkt,
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Stand.objects.get(pk=self.stand1.pk).name, 'My New Name')

    def test_delete(self):
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(Stand.objects.filter(pk=self.stand1.pk).count(), 1)
        response = self.client.delete(self.stand1_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Stand.objects.filter(pk=self.stand1.pk).count(), 0)
        
    def test_show(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.get(self.stand1_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.find('<title>My Stand</title>'), -1)

    def test_unauthorized(self):
        response = self.client.get(self.stand1_url)
        self.assertEqual(response.status_code, 401)

class UserPropertyListTest(TestCase):
    '''
    test web service to grab json of user's properties
    [{fpattrs}, ...]
    '''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_unauth(self):
        url = reverse('trees-user_property_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_jsonlist(self):
        self.client.login(username='featuretest', password='pword')
        url = reverse('trees-user_property_list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        plist = loads(response.content)
        self.assertEquals(plist['features'], [])
        self.assertEquals(plist['bbox'], settings.DEFAULT_EXTENT, plist)

        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        plist = loads(response.content)
        self.assertEquals(plist['features'][0]['properties']['name'], 'My Property')

class PropertyStandListTest(TestCase):
    '''
    test web service to grab json of user's propertie's stands
    [{stand-attrs}, ...]
    '''

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.baduser = User.objects.create_user(
            'baduser', 'baduser@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.prop1.add(self.stand1)
        enable_sharing()

    def test_unauth(self):
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_notexists(self):
        self.client.login(username='baduser', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        url = url.replace(self.prop1.uid, 'trees_forestproperty_123456789')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_baduser(self):
        self.client.login(username='baduser', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) 

    def test_jsonlist(self):
        self.client.login(username='featuretest', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        stand_list = loads(response.content)
        self.assertEquals(stand_list['features'][0]['properties']['name'], 'My Stand', stand_list)

        self.prop1.add(self.stand2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        stand_list = loads(response.content)
        names = [stand['properties']['name'] for stand in stand_list['features']]
        names.sort()
        expected_names = ['My Stand', 'My Stand2']
        expected_names.sort()
        self.assertEqual(names, expected_names)


class ManipulatorsTest(TestCase):
    '''
    test overlap/sliver manipulators
    '''

    def setUp(self):
        '''
        A self-intersecting polyon
        '''
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.bad_ewkt = "SRID=3857;POLYGON((-13738982.554637 5741643.81587,-13748693.674233 \
                5750032.832398,-13740702.387773 5750625.1666924,-13744294.928102 \
                5751848.1591448,-13738982.554637 5741643.81587))"

    def test_clean_badgeom(self):
        self.stand1 = Stand(user=self.user, name="Bad Stand", geometry_orig=self.bad_ewkt) 
        self.stand1.save()
        self.assertTrue(self.stand1.geometry_final.valid)


class SpatialTest(TestCase):
    '''
    Tests the spatial representations of Stands and ForestProperties
    '''

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.prop1.add(self.stand1)

    def test_rest_defaultkml_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('KML')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        errors = kml_errors(response.content)
        self.assertFalse(errors,"invalid KML %s" % str(errors))

    def test_stand_json(self):
        thejson = self.stand1.geojson()
        d = loads(thejson)
        self.assertEquals(d['properties']['name'], 'My Stand')

    def test_property_json(self):
        thejson = self.prop1.feature_set_geojson()
        d = loads(thejson)
        self.assertEquals(len(d['features']), 1)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Stand')
        self.prop1.add(self.stand2)
        thejson = self.prop1.feature_set_geojson()
        d = loads(thejson)
        self.assertEquals(len(d['features']), 2)

    def test_property_bbox(self):
        thejson = self.prop1.feature_set_geojson()
        d = loads(thejson)
        for x, y in zip(d['bbox'], self.prop1.bbox):
            self.assertAlmostEquals(x, y, places=5)

    def test_stand_json_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('GeoJSON')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Stand')
        
    def test_property_json_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Property')

    def test_multistand_json_url(self):
        self.client.login(username='featuretest', password='pword')
        uids = [self.stand1.uid, self.stand2.uid]
        link = Stand.get_options().get_link('GeoJSON')
        url = link.reverse([self.stand1, self.stand2])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(len(d['features']), 2)
        foundit = False
        for f in d['features']:
            if f['properties']['name'] == 'My Stand2':
                foundit = True
        self.assertTrue(foundit)

    def test_property_stands_json_url(self):
        self.prop1.add(self.stand2)
        self.client.login(username='featuretest', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(len(d['features']), 2)
        foundit = False
        for f in d['features']:
            if f['properties']['name'] == 'My Stand2':
                foundit = True
        self.assertTrue(foundit)


class ImputeTest(TestCase):
    fixtures = ['fvs_species_western', ]

    def setUp(self):
        settings.CELERY_ALWAYS_EAGER = True  # force syncronous execution of celery tasks
        import_rasters()
        g2 = GEOSGeometry(
            'SRID=3857;POLYGON((%(x1)s %(y1)s, %(x2)s %(y1)s, %(x2)s %(y2)s, %(x1)s %(y2)s, %(x1)s %(y1)s))' % 
            {'x1': -13841975, 'y1': 5308646, 'x2': -13841703, 'y2': 5308927})
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g2) 
        self.stand1.save()
        self.pk1 = self.stand1.pk

        self.elev = RasterDataset.objects.get(name="elevation")
        self.aspect = RasterDataset.objects.get(name="aspect")
        self.cos_aspect = RasterDataset.objects.get(name="cos_aspect")
        self.sin_aspect = RasterDataset.objects.get(name="sin_aspect")
        self.slope = RasterDataset.objects.get(name="slope")
        self.avg_elev = 145.05799999

    def test_impute_onsave(self):
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertNotEqual(s1.elevation, None)
        self.assertAlmostEqual(s1.elevation, self.avg_elev)

    def test_impute_smart_save(self):
        d = os.path.dirname(__file__)
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertNotEqual(s1.elevation, None)
        self.assertAlmostEqual(s1.elevation, self.avg_elev)
        elev_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'elevationx2.tif')) # swap raster to elevation x 2
        self.elev.filepath = elev_path
        self.elev.save() 
        s1.save()  # saving stand should trigger re-imputing
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertNotEqual(s1.elevation, None)
        self.assertAlmostEqual(s1.elevation, self.avg_elev * 2, places=5) # now we should get a new elevation value  
        elev_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'elevation.tif')) # swap rasters back to normal elevation
        self.elev.filepath = elev_path
        self.elev.save()
        s1.save()  # saving stand should trigger re-imputing
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertNotEqual(s1.elevation, None)
        self.assertAlmostEqual(s1.elevation, self.avg_elev) # back to the original elevation value

    def test_raster_not_found(self):
        self.elev.delete()
        s1 = Stand.objects.get(pk=self.pk1)
        s1.save()
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertEquals(s1.elevation, None)

    def test_zonal_null(self):
        s1 = Stand.objects.get(pk=self.pk1)
        offgeom = GEOSGeometry(
            'SRID=3857;POLYGON((-120.42 34.37, -119.64 34.32, -119.63 34.12, -120.44 34.15, -120.42 34.37))')
        s1.geometry_final = offgeom # this geom should be off the elevation map
        s1.save()
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertEqual(s1.elevation, None)


class StandImportTest(TestCase):
    '''
    TODO test bad shapefiles (other geom types, bad mapping dict, projection)
    TODO assert that mapped attributes are populated
    TODO strata from shp
    '''
    def setUp(self):
        import_rasters()
        d = os.path.dirname(__file__)
        self.shp_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.shp'))
        self.bad_shp_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands_bad.shp'))
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()

    def test_shp_exists(self):
        self.assertTrue(os.path.exists(self.shp_path), self.shp_path)

    def test_importer_py(self):
        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

        s = StandImporter(self.user)
        s.import_ogr(self.shp_path, forest_property=self.prop1) 

        self.assertEqual(len(Stand.objects.all()), 37)
        # from the default 'name' field this time
        self.assertEqual(len(Stand.objects.filter(name='001A')), 0) 
        self.assertEqual(len(Stand.objects.filter(name='277')), 1) 
        self.assertEqual(len(self.prop1.feature_set()), 37)

    def test_importer_py_newproperty(self):
        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

        s = StandImporter(self.user)
        s.import_ogr(self.shp_path, new_property_name="Another Property") 

        self.assertEqual(len(Stand.objects.all()), 37)
        # from the default 'name' field this time
        self.assertEqual(len(Stand.objects.filter(name='001A')), 0) 
        self.assertEqual(len(Stand.objects.filter(name='277')), 1) 
        self.assertEqual(len(self.prop1.feature_set()), 0)
        new_stand = ForestProperty.objects.get(name="Another Property")
        self.assertEqual(len(new_stand.feature_set()), 37)

    def test_importer_py_fieldmap(self):
        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

        s = StandImporter(self.user)
        field_mapping = {'name': 'STAND_TEXT'}
        s.import_ogr(self.shp_path, field_mapping, forest_property=self.prop1) 

        self.assertEqual(len(Stand.objects.all()), 37)
        # from the 'STAND_TEXT' field this time
        self.assertEqual(len(Stand.objects.filter(name='001A')), 1) 
        self.assertEqual(len(Stand.objects.filter(name='277')), 0) 
        self.assertEqual(len(self.prop1.feature_set()), 37)

    def test_importer_multi(self):
        '''
        Test for handling of multipart polygons
        '''
        d = os.path.dirname(__file__)
        multi_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 'testdata', 'test_stands_multi.zip'))
        url = reverse('trees-upload_stands')
        self.client.login(username='featuretest', password='pword')

        with open(multi_path) as f:
            response = self.client.post(url, {'new_property_name': 'Test Multi', 'ogrfile': f})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(len(Stand.objects.all()), 27)
        prop = ForestProperty.objects.get(name="Test Multi")
        self.assertEqual(len(prop.geometry_final), 2)

    def test_importer_holes(self):
        '''
        Test for handling of slivers
        '''
        d = os.path.dirname(__file__)
        holes_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 'testdata', 'test_stands_holes.zip'))
        url = reverse('trees-upload_stands')
        self.client.login(username='featuretest', password='pword')

        # With default threshold, the "sliver" should not show up
        with open(holes_path) as f:
            response = self.client.post(url, {'new_property_name': 'holes', 'ogrfile': f})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(len(Stand.objects.all()), 35)
        prop = ForestProperty.objects.get(name="holes")
        self.assertEqual(prop.geometry_final[0].num_interior_rings, 1)

        # Now try it with a tighter tolerance, the "sliver" should show up as another interior ring
        Stand.objects.all().delete()
        settings.SLIVER_THRESHOLD = 1.0
        with open(holes_path) as f:
            response = self.client.post(url, {'new_property_name': 'holes2', 'ogrfile': f})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(len(Stand.objects.all()), 35)
        prop2 = ForestProperty.objects.get(name="holes2")
        self.assertEqual(prop2.geometry_final[0].num_interior_rings, 2)

    def test_importer_http(self):
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': self.prop1.pk, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertNotEqual(response.content.find('X-Madrona-Select'), -1, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 37)

    def test_importer_http_unauth(self):
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': self.prop1.pk, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(self.prop1.feature_set()), 0)

    def test_importer_http_noname(self):
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands_noname.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': self.prop1.pk, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 500, response.content)
        self.assertNotEqual(response.content.find('Dataset does not have a required field'), -1, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 0)

    def test_importer_http_badproperty(self):
        '''
        If no property is found belonging to the user, should get a 404
        '''
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands_bad.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': 8675309, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 0)

    def test_importer_http_newproperty(self):
        '''
        If no property is found belonging to the user, should get a 404
        '''
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'new_property_name': 'Another Property', 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertNotEqual(response.content.find('X-Madrona-Select'), -1, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 0)
        new_stand = ForestProperty.objects.get(name="Another Property")
        self.assertEqual(len(new_stand.feature_set()), 37)


class GrowthYieldTest(TestCase):
    '''
    # Test via python API 
    self.prop = ForestProperty(..)
    self.prop.run_gy()

    # Test via REST API
    link = self.stand1.options.get_link('Grow')
    url = link.reverse(self.prop)
    response = self.client.post(url)
    # check that reponse is OK ("Scheduling has commenced..")
    '''
    pass

class AdjacencyTest(TestCase):
    '''
    Test that stand adjacency can be reliably determined
    self.prop = ForestProperty(..)
    adj = self.prop.adjacency 
    # @property method with caching
    # returns what? list or txt or file handle? 
    # does it also check for slivers or overlap? 

    needs fixture
    '''
    def setUp(self):
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()

        d = os.path.dirname(__file__)
        self.shp_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.shp'))
        s = StandImporter(self.user)
        s.import_ogr(self.shp_path, forest_property=self.prop1) 

    def test_adjacency(self):
        '''
        stand is adjacent to 332, 336, 405 and 412
        using default threshold of 1.0
        '''
        test_stand = Stand.objects.get(name='397')
        adj_stands = [Stand.objects.get(name=str(x)) for x in [332, 336, 405, 412]]
        adj = self.prop1.adjacency()
        for adj_stand in adj_stands:
            self.assertTrue(adj_stand.pk in adj[test_stand.pk])

    def test_adjacency_threshold(self):
        '''
        stand should be within 100 meters of 425 as well
        '''
        test_stand = Stand.objects.get(name='397')
        adj_stands = [Stand.objects.get(name=str(x)) for x in [332, 336, 405, 412, 425]]
        adj = self.prop1.adjacency(100.0)
        for adj_stand in adj_stands:
            self.assertTrue(adj_stand.pk in adj[test_stand.pk])

class SchedulerTest(TestCase):
    '''
    # Test via python API 
    self.prop.schedule()

    # Test via REST API
    link = self.stand1.options.get_link('Schedule')
    url = link.reverse(self.prop)
    response = self.client.post(url)
    # check that reponse is OK ("Scheduling has commenced..")

    cases:
    manual scheduling without proper stand attributes
    '''
    pass

class OutputsTest(TestCase):
    '''
    After GY and Scheduling, parse the tree list and 
    generate/store as json data associated with
    the stand or property as appropos

    - harvest schedule
    - yield over time
    - standing timber over time
    - carbon
    '''
    def setUp(self):
        '''
        self.prop = ForestProperty(..)
        self.prop.run_gy()
        self.prop.schedule()
        '''
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_property_files(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()
        path = os.path.join(prop1.file_dir, 'test.txt')
        try:
            fh = open(path, 'w')
            fh.write("prop1")
            fh.close()
        except:
            self.fail("Could not write file to " + path)
        os.remove(path)

    def test_yield(self):
        '''
        self.prop.generate('yield_over_time') 
        self.assertTrue(self.prop.outputs.yield['2085'] == 28000)
        '''
        pass

class LocationTest(TestCase):
    fixtures = ['test_counties.json',]

    def setUp(self):
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.realloc = ("Curry", "OR")

    def test_location(self):
        self.assertEqual(len(County.objects.all()), 2, "Counties fixture didn't load properly!")
        self.assertEqual(self.prop1.location, self.realloc)

    def test_bad_location(self):
        self.assertEqual(self.prop1.location, self.realloc)
        cntr = GEOSGeometry('SRID=3857;POINT(-438474.0 980123.1)') # not on the map
        g1 = cntr.buffer(75)
        g1.transform(settings.GEOMETRY_DB_SRID)
        p1 = MultiPolygon(g1)
        self.prop1.geometry_final = p1 
        self.prop1.save()
        self.assertEqual(self.prop1.location, (None, None))

class VariantTest(TestCase):
    fixtures = ['test_fvs_variants.json',]

    def setUp(self):
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.real = "Klamath Mountains"

    def test_variant(self):
        self.assertEqual(len(FVSVariant.objects.all()), 1, "Variant fixture didn't load properly!")
        self.assertEqual(self.prop1.variant, self.real)

    def test_bad_variant(self):
        self.assertEqual(self.prop1.variant, self.real)
        cntr = GEOSGeometry('SRID=3857;POINT(-438474.0 980123.1)') # not on the map
        g1 = cntr.buffer(75)
        g1.transform(settings.GEOMETRY_DB_SRID)
        p1 = MultiPolygon(g1)
        self.prop1.geometry_final = p1 
        self.prop1.save()
        self.assertEqual(self.prop1.variant, None)

class SearchTest(TestCase):
    
    def setUp(self):
        self.searches = [
            ('Tyron Creek', 200, [-13654088.17, 5688345.48]),
            ('41.12345;-81.98765', 200, [-9126823, 5030567]),
            ('39.3 N 76.4 W', 200, [-8504809, 4764735]), 
            ('KJHASBUNCHOFNONSENSEDOIHJJDHSGF', 404, None),
        ]

    def test_no_search(self):
        url = reverse('trees-geosearch')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_search(self):
        from urllib import quote_plus
        baseurl = reverse('trees-geosearch')
        for search in self.searches:
            url = baseurl + "?search=" + quote_plus(search[0])
            response = self.client.get(url)
            self.assertEqual(response.status_code, search[1])
            content = loads(response.content)
            if content['center'] is None:
                self.assertEquals(search[2], None)
            else:
                for x, y in zip(content['center'], search[2]):
                    self.assertAlmostEquals(x, y, delta=3)  # within 3 meters of expected

class ScenarioTest(TestCase):

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand 1", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand 2", geometry_orig=g1) 
        self.stand2.save()
        self.stand3 = Stand(user=self.user, name="My Stand 3 (not on property)", geometry_orig=g1) 
        self.stand3.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.prop1.add(self.stand1)
        self.prop1.add(self.stand2)

        self.options = Scenario.get_options()
        self.create_url = self.options.get_create_form()
        self.geojson_link = self.options.get_link('GeoJSON')

        enable_sharing()

    def test_create_scenario(self):
        s1 = Scenario(user=self.user, name="My Scenario", 
                input_target_boardfeet=2000,
                input_target_carbon=1,
                input_property=self.prop1,
                input_rxs={self.stand1.pk: 'CC', self.stand2.pk: "SW"},
             )
        s1.save()
        self.assertEquals(Scenario.objects.get(name="My Scenario").input_target_boardfeet, 2000.0)

    def test_scenario_results(self):
        s1 = Scenario(user=self.user, name="My Scenario", 
                input_target_boardfeet=2000,
                input_target_carbon=1,
                input_property=self.prop1,
                input_rxs={self.stand1.pk: 'CC', self.stand2.pk: "SW"},
             )
        s1.save()
        out = s1.output_scheduler_results
        results = out[self.stand1.pk]
        self.assertTrue(len(results['carbon']) == len(results['carbon']) ==len(results['carbon']))

    def test_post(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.create_url, {
            'name': "My Scenario", 
            'input_target_boardfeet': 2000,
            'input_target_carbon': 1,
            'input_age_class': 1,
            'input_site_diversity': 1,
            'input_property': self.prop1.pk,
            'input_rxs': dumps({self.stand1.pk: 'CC', self.stand2.pk: "SW"}),
        })
        self.assertEqual(response.status_code, 201)
        
    def test_post_invalid_rx(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.create_url, {
            'name': "My Scenario", 
            'input_target_boardfeet': 2000,
            'input_target_carbon': 1,
            'input_age_class': 1,
            'input_site_diversity': 1,
            'input_property': self.prop1.pk,
            'input_rxs': dumps({self.stand1.pk: 'BAD', self.stand2.pk: "SW"}),
        })
        self.assertEqual(response.status_code, 400, response.content)

    def test_post_invalid_stand(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.create_url, {
            'name': "My Scenario", 
            'input_target_boardfeet': 2000,
            'input_target_carbon': 1,
            'input_age_class': 1,
            'input_site_diversity': 1,
            'input_property': self.prop1.pk,
            'input_rxs': dumps({self.stand3.pk: 'CC', self.stand2.pk: "SW"}),
        })
        self.assertEqual(response.status_code, 400, response.content)

    def test_geojson_results(self):
        s1 = Scenario(user=self.user, name="My Scenario", 
                input_target_boardfeet=2000,
                input_target_carbon=1,
                input_property=self.prop1,
                input_rxs={self.stand1.pk: 'CC', self.stand2.pk: "SW"},
             )
        s1.save()
        url = self.geojson_link.reverse(s1)
        # not logged in yet
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401, response.content)
        # now we log in
        self.client.login(username='featuretest', password='pword')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        # make sure response is good
        res = loads(response.content) 
        results = res['features'][0]['properties']['results']
        self.assertTrue(len(results['carbon']) == len(results['carbon']) ==len(results['carbon']))
        with self.assertRaises(KeyError):
            results['non existent'][0]
        with self.assertRaises(IndexError):
            results['timber'][200]

class AspectTest(TestCase):
    def test_aspect(self):
        from trees.utils import classify_aspect
        aspect_examples = [
          (355, 'North'),
          (2, 'North'),
          (22.4, 'North'),
          (22.6, 'North-East'),
          (45, 'North-East'),
          (216, 'South-West'),
          (355 + 360, 'North'),
        ]
        for ae in aspect_examples:
            self.assertEquals(classify_aspect(ae[0]), ae[1], ae[0])

class SVSTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.baseurl = "/trees/gnn2svs"

    def test_get(self):
        url = "%s/%s/" % (self.baseurl, 2222)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)

class NearestPlotPyTest(TestCase):
    fixtures = ['test_treelive_summary', 'test_idb_summary']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()

    def _create_strata(self):
        stand_list = {
            'classes': [
                ('Douglas-fir', 10, 14, 31),
            ]
        }
        strata = Strata(user=self.user, name="My Strata", search_age=30.0, search_tpa=120.0, stand_list = stand_list)
        strata.save()
        return strata

    def test_bad_stand_list(self):
        stand_list = [ ('Douglas-fir', 10, 14, 31), ] 
        strata = Strata(user=self.user, name="My Strata", search_age=30.0, search_tpa=120.0, stand_list = stand_list)
        with self.assertRaises(Exception):
            strata.save()

        stand_list = {
            'classes': [
                ('Douglas-fir', "booo"),
            ]
        }
        strata = Strata(user=self.user, name="My Strata", search_age=30.0, search_tpa=120.0, stand_list = stand_list)
        with self.assertRaises(Exception):
            strata.save()

    def test_assign_strata_to_stand(self):
        strata = self._create_strata()
        self.assertTrue(strata)
        self.stand1.strata = strata
        self.assertEqual("My Strata", self.stand1.strata.name)

    def test_find_candidates_for_strata(self):
        strata = self._create_strata()
        self.assertTrue(1 in [x[0] for x in strata.candidates(1).iterrows()])
        self.assertTrue(2 in [x[0] for x in strata.candidates(1).iterrows()])

    def test_nearest(self):
        strata = self._create_strata()
        import_rasters()
        self.assertTrue(strata)
        self.stand1.strata = strata
        self.stand1.save()
        self.assertEquals(self.stand1.cond_id, None)
        self.assertTrue(1 in [x[0] for x in strata.candidates(1).iterrows()])
        self.assertTrue(2 in [x[0] for x in strata.candidates(1).iterrows()])
        self.assertEquals(self.stand1.get_idb().pk, 1)
        self.assertEquals(self.stand1.cond_id, 1)

class NearestPlotRestTest(TestCase):
    fixtures = ['test_treelive_summary', 'test_idb_summary']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        enable_sharing()

    def test_standstrata_workflow(self):
        self.client.login(username='featuretest', password='pword')

        ##### Step 1. Create the property
        old_count = ForestProperty.objects.count()
        url = "/features/forestproperty/form/"
        response = self.client.post( url,
            {   
                'name': 'test property', 
                'geometry_final': p1.wkt,  # multipolygon required
            }
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(old_count < ForestProperty.objects.count())
        prop1 = ForestProperty.objects.get(name="test property")

        #### Step 2. Create the stand
        old_count = Stand.objects.count()
        url = "/features/stand/form/"
        response = self.client.post( url, 
            {   
                'name': 'test stand', 
                'geometry_orig': g1.wkt, 
            }
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(old_count < Stand.objects.count())
        stand1 = Stand.objects.get(name="test stand")

        #### Step 2b. Associate the stand with the property
        url = "/features/forestproperty/%s/add/%s" % (prop1.uid, stand1.uid)
        response = self.client.post( url, {} )
        self.assertEqual(response.status_code, 200, response.content)

        #### Step 3. Create the strata
        old_count = Strata.objects.count()
        url = "/features/strata/form/"
        response = self.client.post( url, 
            {
                'name': 'test strata', 
                'search_tpa': 160,
                'search_age': 40,
                'stand_list': u'{"classes":[["Douglas-fir",5,10,5],["Douglas-fir",10,15,50]]}'
                # see https://github.com/Ecotrust/land_owner_tools/wiki/Stand-List
            }
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(old_count < Strata.objects.count())
        strata1 = Strata.objects.get(name="test strata")

        #### Step 3b. Associate the strata with the property
        url = "/features/forestproperty/%s/add/%s" % (prop1.uid, strata1.uid)
        response = self.client.post( url,
            {}   
        )
        self.assertEqual(response.status_code, 200, response.content)

        #### Step 4. Add the stand to a strata
        url = "/features/strata/links/add-stands/%s/" % strata1.uid
        response = self.client.post( url, 
            { 'stands': ",".join([stand1.uid]) }   
        )
        self.assertEqual(response.status_code, 200, response.content)
        stand1b = Stand.objects.get(name="test stand")
        self.assertEqual(stand1b.strata, strata1)

        #### Step 5. Get the list of strata for the property
        url = "/trees/strata_list/%s/" % prop1.uid
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        rd = json.loads(response.content)
        self.assertEqual(len(rd),1)
        self.assertEqual(rd[0]['name'], 'test strata')
        self.assertEqual(rd[0]['search_tpa'], 160.0)
