# main.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime

# استيراد من الملف الأساسي
from compression import (
    PlayerDatabase, Player, Sport, Level, Physical, 
    Technical, Experience, GroqComparisonEngine, OverallEngine,
    PositionEngine, PlayerDataParser, OUTPUT_DIR
)

router = APIRouter()

_COMPRESSION_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize database
db = PlayerDatabase()
comparison_engine = GroqComparisonEngine()

# Load players
db.load_from_knowledge_file(os.path.join(_COMPRESSION_DIR, "players.json"))

# Pydantic models
class PlayerCreate(BaseModel):
    name: str
    sport: str
    position: str
    age: int
    height: float
    weight: float
    physical: dict
    technical: dict
    experience: dict

class PlayerResponse(BaseModel):
    id: int
    name: str
    sport: str
    position: str
    age: int
    height: float
    weight: float
    physical: dict
    technical: dict
    experience: dict

class CompareRequest(BaseModel):
    player1_id: int
    player2_id: int

class PlayerSummary(BaseModel):
    id: int
    name: str
    sport: str
    position: str
    age: int

@router.get("/")
async def root():
    return {
        "message": "Player Comparison API",
        "version": "1.0.0",
        "description": "Compare sports players using AI-powered analysis",
        "output_directory": OUTPUT_DIR,
        "endpoints": {
            "/players": "Get all players",
            "/players/{id}": "Get player by ID",
            "/players/search": "Search players by name",
            "/players/exact/{name}": "Search players by exact name",
            "/players/sport/{sport}": "Get players by sport",
            "/players/add": "Add a new player (POST)",
            "/players/compare": "Compare two players (POST)",
            "/players/compare/pdf": "Get PDF comparison report (POST)",
            "/players/bulk": "Bulk upload players from players.json (POST)",
            "/players/stats/{id}": "Get detailed player stats"
        }
    }

@router.get("/players", response_model=List[PlayerSummary])
async def get_players():
    """Get all players"""
    return db.get_players_summary()

@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int):
    """Get player by ID"""
    player = db.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return {
        "id": player.player_id,
        "name": player.name,
        "sport": player.sport.value,
        "position": player.position,
        "age": player.age,
        "height": player.height,
        "weight": player.weight,
        "physical": player.physical.__dict__,
        "technical": player.technical.__dict__,
        "experience": {
            "years": player.experience.years,
            "matches": player.experience.matches,
            "training_days": player.experience.training_days,
            "level": player.experience.level.value
        }
    }

@router.get("/players/search")
async def search_players(name: str = Query(..., min_length=1, description="Name or part of name to search")):
    """Search players by name (partial match)"""
    results = db.search_by_name(name)
    return [{
        "id": p.player_id,
        "name": p.name,
        "sport": p.sport.value,
        "position": p.position,
        "age": p.age
    } for p in results]

@router.get("/players/exact/{name}")
async def search_players_exact(name: str):
    """Search players by exact name match"""
    results = db.search_by_exact_name(name)
    return [{
        "id": p.player_id,
        "name": p.name,
        "sport": p.sport.value,
        "position": p.position,
        "age": p.age
    } for p in results]

@router.get("/players/sport/{sport}")
async def get_players_by_sport(sport: str):
    """Get players by sport"""
    sport_map = {
        "football": Sport.FOOTBALL,
        "basketball": Sport.BASKETBALL,
        "handball": Sport.HANDBALL,
        "volleyball": Sport.VOLLEYBALL
    }
    
    sport_enum = sport_map.get(sport.lower())
    if not sport_enum:
        raise HTTPException(status_code=400, detail="Invalid sport. Available: football, basketball, handball, volleyball")
    
    results = db.search_by_sport(sport_enum)
    return [{
        "id": p.player_id,
        "name": p.name,
        "sport": p.sport.value,
        "position": p.position,
        "age": p.age
    } for p in results]

@router.post("/players/add")
async def add_player(player_data: PlayerCreate):
    """Add a new player"""
    try:
        sport_map = {
            "Football": Sport.FOOTBALL,
            "Basketball": Sport.BASKETBALL,
            "Handball": Sport.HANDBALL,
            "Volleyball": Sport.VOLLEYBALL
        }
        
        level_map = {
            "Beginner": Level.BEGINNER,
            "Intermediate": Level.INTERMEDIATE,
            "Advanced": Level.ADVANCED
        }
        
        physical = Physical(**player_data.physical)
        technical = Technical(**player_data.technical)
        experience = Experience(
            years=player_data.experience.get('years', 5),
            matches=player_data.experience.get('matches', 100),
            training_days=player_data.experience.get('training_days', 4),
            level=level_map.get(player_data.experience.get('level', 'Intermediate'), Level.INTERMEDIATE)
        )
        
        player = Player(
            player_id=0,
            name=player_data.name,
            sport=sport_map.get(player_data.sport, Sport.FOOTBALL),
            position=player_data.position,
            age=player_data.age,
            height=player_data.height,
            weight=player_data.weight,
            physical=physical,
            technical=technical,
            experience=experience
        )
        
        player_id = db.add_player(player)
        return {"message": "Player added successfully", "id": player_id}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/players/bulk")
async def bulk_upload_players():
    """Bulk upload players from players.json"""
    try:
        db.load_from_knowledge_file(os.path.join(_COMPRESSION_DIR, "players.json"))
        return {
            "message": "Players loaded successfully",
            "total_players": len(db.get_all_players())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/players/compare")
async def compare_players(request: CompareRequest):
    """Compare two players and return JSON analysis"""
    player1 = db.get_player(request.player1_id)
    player2 = db.get_player(request.player2_id)
    
    if not player1:
        raise HTTPException(status_code=404, detail="Player 1 not found")
    if not player2:
        raise HTTPException(status_code=404, detail="Player 2 not found")
    
    if player1.sport != player2.sport:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot compare different sports: {player1.sport.value} vs {player2.sport.value}"
        )
    
    result = comparison_engine.compare(player1, player2)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/players/compare/pdf")
async def compare_players_pdf(request: CompareRequest):
    """Compare two players and return a PDF report"""
    player1 = db.get_player(request.player1_id)
    player2 = db.get_player(request.player2_id)
    
    if not player1:
        raise HTTPException(status_code=404, detail="Player 1 not found")
    if not player2:
        raise HTTPException(status_code=404, detail="Player 2 not found")
    
    if player1.sport != player2.sport:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot compare different sports: {player1.sport.value} vs {player2.sport.value}"
        )
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name1 = comparison_engine._sanitize_filename(player1.name)
        clean_name2 = comparison_engine._sanitize_filename(player2.name)
        filename = f"comparison_report_{clean_name1}_{clean_name2}_{timestamp}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, filename)
        
        output_path = comparison_engine.generate_pdf_report(player1, player2, pdf_path)
        
        if output_path and os.path.exists(output_path):
            return FileResponse(
                output_path,
                media_type="application/pdf",
                filename=os.path.basename(output_path)
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players/stats/{player_id}")
async def get_player_stats(player_id: int):
    """Get detailed stats for a player including overall and position scores"""
    player = db.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    overall_engine = OverallEngine()
    position_engine = PositionEngine()
    
    overall_score = overall_engine.calculate(player)
    position_result = position_engine.calculate(player)
    
    return {
        "player": {
            "id": player.player_id,
            "name": player.name,
            "sport": player.sport.value,
            "position": player.position
        },
        "overall_score": overall_score,
        "position_score": position_result["position_score"],
        "position_details": position_result["details"]
    }

@router.delete("/players/{player_id}")
async def delete_player(player_id: int):
    """Delete a player by ID"""
    player = db.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    del db.players[player_id]
    return {"message": f"Player {player_id} deleted successfully"}
