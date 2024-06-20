from typing import List

import uvicorn
from fastapi import FastAPI, Path, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, String, Integer, select, update, asc
from sqlalchemy.orm import DeclarativeBase, sessionmaker,Mapped, mapped_column



# Utility function to set attributes on an object from a dictionary
def set_attrs(obj, data: dict):
    if data:
        for key, value in data.items():
            setattr(obj, key, value)


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Database connection string (consider using environment variables in production)
engine = create_engine('mysql+pymysql://DevUser:Password@localhost/DevDb,echo=True)


# Define the OrderTeaEntity model representing the "order_teas" table
class OrderTeaEntity(Base):
    __tablename__ = "order_teas"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tea_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    order_name: Mapped[str] = mapped_column(String(10), nullable=False)


# Create the tables in the database
Base.metadata.create_all(engine)

# Create a sessionmaker bound to the engine
Session = sessionmaker(bind=engine)

# Initialize FastAPI application
contact = {
    "name" : "Drink_Menu",
    "url" : "https://www.pret.co.uk/en-GB/products/categories/hot-drinks"
}


app = FastAPI(title=' Infrastructure Team Cafe Time Tea Order API',
              description='''Every Friday, colleagues are welcome to order drinks 
                            between 3-5pm, and everyone can sit down and chat 
                            about interesting things that happened at work 
                            this week in SUN meeting room.''',
              version='1.0',
              contact=contact)

# Define API models
class OrderTeaBase(BaseModel):
    tea_name: str
    order_name: str


class OrderTeaCreate(OrderTeaBase):
    ...


class OrderTeaUpdate(OrderTeaBase):
    ...


class OrderTeaOut(OrderTeaBase):
    order_id: int

# Dependency to get a database session
def get_db_session():
    db_session = Session()

    try:
        yield db_session
    finally:
        db_session.close()

# Endpoint to get a list of all Order Tea
@app.get('/order_teas', tags=["Query All Tea Orders"], response_model=List[OrderTeaOut])
async def get_order_teas(db_session: Session = Depends(get_db_session)):
    query = select(OrderTeaEntity).order_by(asc(OrderTeaEntity.order_name))
    return db_session.execute(query).scalars().all()


# Endpoint to create a new order_teas
@app.post('/order_teas', tags=["Add Tea Order"], response_model=OrderTeaOut)
async def create_ordertea(order_teas: OrderTeaCreate, db_session: Session = Depends(get_db_session)):
    # Check if the Order_tea already exists
    query = select(OrderTeaEntity).where(OrderTeaEntity.order_name == order_teas.order_name)
    records = db_session.execute(query).scalars().all()
    if records:
        raise HTTPException(status_code=400, detail=f'Order Tea {order_teas.order_name} already exists')
    
    # Create a new Order Tea record
    orderteas_entity = OrderTeaEntity(tea_name=order_teas.tea_name, order_name=order_teas.order_name)
    db_session.add(orderteas_entity)
    db_session.commit()
    
    return orderteas_entity


def check_ordertea_exist(order_id: int, db_session: Session):
    query = select(OrderTeaEntity).where(OrderTeaEntity.order_id == order_id)
    exist_ordertea = db_session.execute(query).scalar()
    if not exist_ordertea:
       raise HTTPException(status_code=404, detail=f'Order id({order_id}) not found')
   
    return exist_ordertea


# Endpoint to update an existing student
@app.put('/order_teas/{order_id}', tags=["Modify Tea Order"], response_model=OrderTeaOut)
async def update_ordertea(*, order_id: int = Path(...), order_teas: OrderTeaUpdate,
                        db_session: Session = Depends(get_db_session)):
    exist_ordertea = check_ordertea_exist(order_id, db_session)
    
    set_attrs(exist_ordertea, order_teas.model_dump())
    
    db_session.commit()
    
    return exist_ordertea


@app.delete('/order_teas/{order_id}', tags=["Delete Tea Order"], response_model=OrderTeaOut)
async def delete_student(order_id: int = Path(...), db_session: Session = Depends(get_db_session)):
    exist_ordertea = check_ordertea_exist(order_id, db_session)
    
    db_session.delete(exist_ordertea)
    
    db_session.commit()
    
    return exist_ordertea


if __name__ == '__main__':
    uvicorn.run("order_teas_crud:app", reload=True)
