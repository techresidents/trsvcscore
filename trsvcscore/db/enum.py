import collections
import logging 
import time

class EnumDict(dict):
    def __init__(self, enum_class, dict_attribute, *args, **kwargs):
        self.enum_class = enum_class
        self.dict_attribute = dict_attribute
        super(EnumDict, self).__init__(*args, **kwargs)
    
    def __missing__(self, key):
        if self.enum_class.can_load():
            try:
                self.enum_class.load()
            except Exception as error:
                logging.exception(error)
        
        d = getattr(self.enum_class, self.dict_attribute)
        if key not in d:
            msg = "no such key '%s'" % key
            raise KeyError(msg)
        
        return d[key]
        
class EnumMeta(type):
    def __new__(cls, name, bases, attributes):

        #create new class
        new_class = super(EnumMeta, cls).__new__(cls, name, bases, {})

        new_class.load_timestamp = 0
        new_class.uppercase_properties = False

        new_class.KEYS_TO_VALUES = EnumDict(new_class, 'KEYS_TO_VALUES')
        new_class.VALUES_TO_KEYS = EnumDict(new_class, 'VALUES_TO_KEYS')
        new_class.PROPERTIES_TO_VALUES = EnumDict(
                new_class, 'PRPOERTIES_TO_VALUES')
        
        if not attributes.get("base", False):
            required = [
                "model_class",
                "key_column",
                "value_column",
                "db_session_factory"
            ]
            
            for attribute in required:
                if attribute not in attributes:
                    raise RuntimeError("'%s' attribute required" % attribute) 

        #Add class attributes to new class
        for name, value in attributes.items():
            new_class.add_to_class(name, value)
        
        try:
            if "base" not in attributes:
                new_class.load()
        except Exception as error:
            logging.exception(error)

        return new_class

    def __getattr__(cls, attribute):
        found = attribute in cls.PROPERTIES_TO_VALUES or \
                attribute in cls.KEYS_TO_VALUES

        if (not found or cls.expired()) and cls.can_load():
            try:
                cls.load()
            except Exception as error:
                logging.exception(error)
        
        if attribute not in cls.PROPERTIES_TO_VALUES:
            if attribute not in cls.KEYS_TO_VALUES:
                msg = "no such attribute '%s'" % attribute
                raise AttributeError(msg)
            else:
                result = cls.KEYS_TO_VALUES[attribute]
        else:
            result = cls.PROPERTIES_TO_VALUES[attribute]

        return result

    def add_to_class(cls, name, value):
        if hasattr(value, "contribute_to_class"):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)
    
    def expired(cls):
        elapsed = time.time() - cls.load_timestamp
        return elapsed > cls.expire
    
    def can_load(cls):
        elapsed = time.time() - cls.load_timestamp
        return elapsed > cls.throttle

    def load(cls):
        try:
            cls.load_timestamp = time.time()

            session = None
            keys_to_values = {} 
            values_to_keys = {}
            properties_to_values = {}

            session = cls.db_session_factory()
            models = session.query(cls.model_class).all()
            for model in models:
                key = getattr(model, cls.key_column)
                value = getattr(model, cls.value_column)
                keys_to_values[key] = value
                values_to_keys[value] = key
            
            for key, value in keys_to_values.iteritems():
                prop = key.replace(" ", "_")
                if cls.uppercase_properties:
                    prop = prop.upper()
                properties_to_values[prop] = value
            
            cls.KEYS_TO_VALUES = EnumDict(cls, 'KEYS_TO_VALUES', keys_to_values)
            cls.VALUES_TO_KEYS = EnumDict(cls, 'VALUES_TO_KEYS', values_to_keys)
            cls.PROPERTIES_TO_VALUES = EnumDict(
                    cls, 'PROPERTIES_TO_VALUES', properties_to_values)

            session.commit()

        except Exception:
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()


class Enum(object):
    __metaclass__ = EnumMeta
    base = True
    expire = 3600
    throttle = 60
    def __init__(*args, **kwargs):
        raise RuntimeError("Enum should not be instantiated")
