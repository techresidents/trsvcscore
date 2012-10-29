import logging 

class EnumMeta(type):
    def __new__(cls, name, bases, attributes):

        #create new class
        module = attributes.pop("__module__")
        new_class = super(EnumMeta, cls).__new__(
                cls,
                name,
                bases,
                {"__module__": module})

        new_class.loaded = False
        new_class.KEYS_TO_VALUES = {}
        new_class.VALUES_TO_KEYS = {}
        
        if "base" not in attributes:
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

    def __getattribute__(cls, attribute):
        if attribute in ["KEYS_TO_VALUES", "VALUES_TO_KEYS"]: 
            try:
                if not cls.loaded:
                    cls.load()
            except Exception as error:
                logging.exception(error)

        return super(EnumMeta, cls).__getattribute__(attribute)

    def add_to_class(cls, name, value):
        if hasattr(value, "contribute_to_class"):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)
    
    def load(cls):
        try:
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
            
            cls.loaded = True
            cls.KEYS_TO_VALUES = keys_to_values
            cls.VALUES_TO_KEYS = values_to_keys

            #add class attributes
            for attribute, value in keys_to_values.items():
                setattr(cls, str(attribute).upper(), value)

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
    def __init__(*args, **kwargs):
        raise RuntimeError("Enum should not be instantiated")
