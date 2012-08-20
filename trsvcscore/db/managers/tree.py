class TreeManager(object):
    """SQLAlchemy Tree Manager.

    This manager is intended to be used with self-referential
    models implementing a hierarchy through an adjacency list.
    Once instantiated, this manager provides convenient methods
    for retreiving the entire hierarchy through a single
    recrusive query.

    Note that the model must have the following attributes:
        id: primary key
        parent_id: foreign key to parent node
        
    """


    def __init__(self, model_class):
        """TreeManager constructor

        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class

        self.default_query = \
                """with recursive q as 
                ( select t.*, 1 as level from {0} t where id = :id
                  union all
                  select tc.*, level + 1 from q
                  join {0} tc on tc.parent_id = q.id
                )
                select * from q order by level
                """.format(self.model_class.__tablename__)

        self.by_rank_query = \
                """with recursive q as 
                ( select t.*, 1 as level from {0} t where id = :id
                  union all
                  select tc.*, level + 1 from q
                  join {0} tc on tc.parent_id = q.id
                )
                select * from q order by rank
                """.format(self.model_class.__tablename__)
    
    def tree(self, session, id):
        """Get entire tree through recursive query.

        Args:
            session: SQLAlchemy sesison object
            id: model primary key

        Returns: The entire tree from and including
            the model referenced by 'id'. The tree
            is returned as a list of (level, model)
            tuples ordered by level.
        """
        return session.query(self.model_class)\
                .add_columns("level")\
                .from_statement(self.default_query)\
                .params(id=id).all()

    def tree_by_rank(self, session, id):
        """Get entire tree (ordered by rank) through recursive query.
        
        In additon to the id, parent_id attributes, the 
        model must also have a rank attribute for use
        with this method.

        Args:
            session: SQLAlchemy sesison object
            id: model primary key

        Returns: The entire tree from and including
            the model referenced by 'id'. The tree
            is returned as a list of (level, model)
            tuples ordered by rank.
        """
        return session.query(self.model_class)\
                .add_columns("level")\
                .from_statement(self.by_rank_query)\
                .params(id=id).all()
