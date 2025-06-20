from sqlalchemy import create_engine, ForeignKey, Boolean, Column, Integer, Text, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.ext.mutable import MutableList

from config import DATABASE_URI

engine = create_engine(DATABASE_URI, echo=True)
# 数据库表基类
Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata.naming_convention = naming_convention
# 会话，用于通过ORM操作数据库
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()


class Area(Base):
    __tablename__ = "area"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    svgPath = Column(Text, nullable=False)
    color = Column(Text, nullable=False)
    hoverColor = Column(Text, nullable=False)
    coordinates = Column(MutableList.as_mutable(JSON()), nullable=True, default=[])
    info = Column(Text, nullable=True)
    teachers = Column(MutableList.as_mutable(JSON()), nullable=True, default=[])

    def to_json(self):
        data = {
            "id": self.id,
            "name": self.name,
            "svgPath": self.svgPath,
            "color": self.color,
            "hoverColor": self.hoverColor,
            "coordinates": self.coordinates,
            "info": self.info,
            "teachers": self.teachers,
        }
        return data


# 创建所有表（被alembic替代）
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
