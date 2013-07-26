import logging 
import time

class EnumMeta(type):
    def __new__(cls, name, bases, attributes):

        #create new class
        new_class = super(EnumMeta, cls).__new__(cls, name, bases, {})

        new_class.load_timestamp = 0
        new_class.KEYS_TO_VALUES = {}
        new_class.VALUES_TO_KEYS = {}
        
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
        if cls.should_load(attribute):
            try:
                cls.load()
            except Exception as error:
                logging.exception(error)

        if attribute not in cls.KEYS_TO_VALUES:
            msg = "no such attribute '%s'" % attribute
            raise AttributeError(msg)

        return cls.KEYS_TO_VALUES[attribute]

    def add_to_class(cls, name, value):
        if hasattr(value, "contribute_to_class"):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)
    
    def should_load(cls, attribute):
        result = False
        elapsed = time.time() - cls.load_timestamp
        if attribute in cls.KEYS_TO_VALUES:
            result = elapsed > cls.expire and \
                     elapsed > cls.throttle
        else:
            result = elapsed > cls.throttle

        return result

    def load(cls):
        try:
            cls.load_timestamp = time.time()

            session = None
            keys_to_values = {} 
            values_to_keys = {}

            session = cls.db_session_factory()
            models = session.query(cls.model_class).all()
            for model in models:
                key = getattr(model, cls.key_column)
                value = getattr(model, cls.value_column)
                keys_to_values[key] = value
                values_to_keys[value] = key
            
            cls.KEYS_TO_VALUES = keys_to_values
            cls.VALUES_TO_KEYS = values_to_keys

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
