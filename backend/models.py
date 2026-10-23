from sqlalchemy import (MetaData,Table,Column,Integer,String, Text, Float,
                        Boolean, DateTime, ForeignKey, inspect, text)



SCHEMA = {
    "users": {
        "username": {"type": "str", "max": 50, "required": True, "unique": True},
        "email":    {"type": "str", "max": 100, "required": True, "unique": True},
        "password": {"type": "str", "required": True, "secret": True},
        "age":      {"type": "int"},
        "co2eqkg":      {"type": "int"},

    }
}

TYPES = {"str": String, "text": Text, "int": Integer, "float": Float,
         "bool": Boolean, "datetime": DateTime}
metadata = MetaData()
tables:dict[str,Table]={} 

def build_column(name:str,spec:dict)->Column:
    kind = spec['type']
    coltype = String(spec.get("max",255)) if kind=="str"else TYPES[kind]()
    args = [coltype]
    if "fk" in spec:
        args.append(ForeignKey(spec["fk"]))
    return Column(
        name,*args, nullable = not spec.get("required",False),
        unique = spec.get("unique",False),
        default = spec.get("default"),
    )

for table_name, cols in SCHEMA.items():
    tables[table_name] = Table(
        table_name, metadata,
        Column("id", Integer, primary_key=True),
        *[build_column(n, s) for n, s in cols.items()],
    )

def sync_schema(engine):
    """Create missing tables, and add missing columns to existing ones."""
    metadata.create_all(engine)            # makes app.db + any missing tables
    insp = inspect(engine)
    with engine.begin() as conn:
        for name, table in tables.items():
            existing = {c["name"] for c in insp.get_columns(name)}
            for col in table.columns:
                if col.name not in existing:
                    ddl = col.type.compile(engine.dialect)
                    conn.execute(text(f'ALTER TABLE "{name}" ADD COLUMN "{col.name}" {ddl}'))
                    print(f"+ added column {name}.{col.name}")
