"""
Fachada de modelos Django del dominio clínico.

Los modelos persistentes se encuentran organizados en:

clinica.infrastructure.persistence.models

Este módulo se conserva como punto oficial de
descubrimiento de modelos para Django y para mantener
compatibilidad con migraciones y código histórico.
"""

from .infrastructure.persistence.models import *