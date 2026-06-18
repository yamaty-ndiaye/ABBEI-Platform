from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Bailleur(Base):
    __tablename__ = "bailleurs"
    __table_args__ = {"schema": "activite"}

    id = Column(Integer, primary_key=True)
    code_bailleur = Column(String, unique=True, nullable=False)
    nom = Column(String, nullable=False)
    adresse = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())


class BonCommande(Base):
    __tablename__ = "bons_commande"
    __table_args__ = {"schema": "activite"}

    id = Column(Integer, primary_key=True)
    numero_bc = Column(String, unique=True, nullable=False)
    reference_interne = Column(String)
    bailleur_id = Column(Integer, nullable=False)
    reference_marche = Column(String)
    contact_abbei = Column(String)
    statut = Column(String, default="en_cours")
    source_fichier = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())


class BonIntervention(Base):
    __tablename__ = "bons_intervention"
    __table_args__ = {"schema": "activite"}

    id = Column(Integer, primary_key=True)
    bon_commande_id = Column(Integer, nullable=False)
    numero_intervention = Column(String)
    adresse_chantier = Column(String)
    description_travaux = Column(String)
    metier = Column(String)
    date_debut = Column(Date)
    date_fin = Column(Date)
    statut = Column(String, default="en_cours")
    created_at = Column(TIMESTAMP, server_default=func.now())