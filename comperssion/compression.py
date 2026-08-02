# compression.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

load_dotenv()

# Create output directory if it doesn't exist
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class Sport(Enum):
    FOOTBALL = "Football"
    BASKETBALL = "Basketball"
    HANDBALL = "Handball"
    VOLLEYBALL = "Volleyball"

class Level(Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

@dataclass
class Physical:
    speed: float
    strength: float
    endurance: float
    agility: float
    flexibility: float

@dataclass
class Technical:
    passing: float
    shooting: float
    dribbling: float
    defending: float
    vision: float
    finishing: float

@dataclass
class Experience:
    years: int
    matches: int
    training_days: int
    level: Level

@dataclass
class Player:
    player_id: int
    name: str
    sport: Sport
    position: str
    age: int
    height: float
    weight: float
    physical: Physical
    technical: Technical
    experience: Experience

class PlayerDataParser:
    @staticmethod
    def parse_physical(text: str) -> Dict:
        physical = {}
        patterns = {
            'speed': r'Speed:\s*(\d+)/100',
            'strength': r'Strength:\s*(\d+)/100',
            'agility': r'Agility:\s*(\d+)/100',
            'endurance': r'Endurance:\s*(\d+)/100',
            'flexibility': r'Flexibility:\s*(\d+)/100'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                physical[key] = float(match.group(1)) / 10
            else:
                physical[key] = 5.0
        return physical

    @staticmethod
    def parse_technical(text: str) -> Dict:
        technical = {}
        patterns = {
            'passing': r'Passing:\s*(\d+)/100',
            'shooting': r'Shooting:\s*(\d+)/100',
            'dribbling': r'Dribbling:\s*(\d+)/100',
            'defending': r'Defending:\s*(\d+)/100',
            'vision': r'Vision:\s*(\d+)/100',
            'finishing': r'Finishing:\s*(\d+)/100'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                technical[key] = float(match.group(1)) / 10
            else:
                technical[key] = 5.0
        return technical

    @staticmethod
    def parse_experience(text: str) -> Dict:
        experience = {'years': 5, 'matches': 100, 'training_days': 4, 'level': 'Intermediate'}
        patterns = {
            'years': r'Years of Experience:\s*(\d+)',
            'matches': r'Matches:\s*(\d+)',
            'training_days': r'Training Days/Week:\s*(\d+)',
            'level': r'Level:\s*(\w+)'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == 'level':
                    experience[key] = match.group(1)
                else:
                    experience[key] = int(match.group(1))
        return experience

    @staticmethod
    def parse_player_profile(text: str) -> Optional[Player]:
        try:
            name_match = re.search(r'Full Name:\s*(.+?)(?:\n|$)', text)
            if not name_match:
                return None
            name = name_match.group(1).strip()
            
            sport_match = re.search(r'Sport:\s*(\w+)', text)
            if not sport_match:
                return None
            sport_name = sport_match.group(1).strip()
            
            sport_map = {
                "Football": Sport.FOOTBALL,
                "Basketball": Sport.BASKETBALL,
                "Handball": Sport.HANDBALL,
                "Volleyball": Sport.VOLLEYBALL
            }
            sport = sport_map.get(sport_name)
            if not sport:
                return None
            
            position_match = re.search(r'Primary Position:\s*(.+?)(?:\n|$)', text)
            position = position_match.group(1).strip() if position_match else ""
            
            position_mapping = {
                "Center Forward": "Striker",
                "Right Winger": "Right Winger",
                "Left Winger": "Left Winger",
                "Attacking Midfielder": "Attacking Midfielder",
                "Defensive Midfielder": "Defensive Midfielder",
                "Central Midfielder": "Central Midfielder"
            }
            position = position_mapping.get(position, position)
            
            age_match = re.search(r'Age:\s*(\d+)', text)
            age = int(age_match.group(1)) if age_match else 20
            
            height_match = re.search(r'Height:\s*([\d.]+)m', text)
            height = float(height_match.group(1)) * 100 if height_match else 180.0
            
            weight_match = re.search(r'Weight:\s*(\d+)kg', text)
            weight = float(weight_match.group(1)) if weight_match else 75.0
            
            physical_dict = PlayerDataParser.parse_physical(text)
            technical_dict = PlayerDataParser.parse_technical(text)
            
            physical = Physical(
                speed=physical_dict.get('speed', 5.0),
                strength=physical_dict.get('strength', 5.0),
                endurance=physical_dict.get('endurance', 5.0),
                agility=physical_dict.get('agility', 5.0),
                flexibility=physical_dict.get('flexibility', 5.0)
            )
            
            technical = Technical(
                passing=technical_dict.get('passing', 5.0),
                shooting=technical_dict.get('shooting', 5.0),
                dribbling=technical_dict.get('dribbling', 5.0),
                defending=technical_dict.get('defending', 5.0),
                vision=technical_dict.get('vision', 5.0),
                finishing=technical_dict.get('finishing', 5.0)
            )
            
            exp_dict = PlayerDataParser.parse_experience(text)
            level_map = {
                "Beginner": Level.BEGINNER,
                "Intermediate": Level.INTERMEDIATE,
                "Advanced": Level.ADVANCED
            }
            level = level_map.get(exp_dict.get('level', 'Intermediate'), Level.INTERMEDIATE)
            
            experience = Experience(
                years=exp_dict.get('years', 5),
                matches=exp_dict.get('matches', 100),
                training_days=exp_dict.get('training_days', 4),
                level=level
            )
            
            return Player(
                player_id=0,
                name=name,
                sport=sport,
                position=position,
                age=age,
                height=height,
                weight=weight,
                physical=physical,
                technical=technical,
                experience=experience
            )
        except Exception:
            return None

class PlayerDatabase:
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self._next_id = 1
    
    def add_player(self, player: Player) -> int:
        player.player_id = self._next_id
        self.players[self._next_id] = player
        self._next_id += 1
        return player.player_id
    
    def get_player(self, player_id: int) -> Optional[Player]:
        return self.players.get(player_id)
    
    def search_by_name(self, name: str) -> List[Player]:
        name_lower = name.lower().strip()
        results = []
        for player in self.players.values():
            if name_lower in player.name.lower():
                results.append(player)
        return results
    
    def search_by_exact_name(self, name: str) -> List[Player]:
        name_lower = name.lower().strip()
        results = []
        for player in self.players.values():
            if player.name.lower() == name_lower:
                results.append(player)
        return results
    
    def search_by_sport(self, sport: Sport) -> List[Player]:
        return [p for p in self.players.values() if p.sport == sport]
    
    def get_all_players(self) -> List[Player]:
        return list(self.players.values())
    
    def get_players_summary(self) -> List[Dict]:
        summary = []
        for player in self.players.values():
            summary.append({
                "id": player.player_id,
                "name": player.name,
                "sport": player.sport.value,
                "position": player.position,
                "age": player.age
            })
        return summary
    
    def load_from_knowledge_file(self, filename: str = "players.json"):
        if not os.path.exists(filename):
            print(f"File {filename} not found")
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        profiles = re.split(r'Player Profile \d+', content)
        
        loaded_count = 0
        for profile_text in profiles:
            if not profile_text.strip():
                continue
            player = PlayerDataParser.parse_player_profile(profile_text)
            if player:
                self.add_player(player)
                loaded_count += 1
        
        print(f"Loaded {loaded_count} players from {filename}")

class PhysicalEngine:
    def calculate(self, player):
        p = player.physical
        score = (p.speed * 0.30 + p.strength * 0.25 + p.endurance * 0.20 + 
                p.agility * 0.15 + p.flexibility * 0.10)
        return round(score * 10, 2)

class TechnicalEngine:
    def calculate(self, player):
        t = player.technical
        score = (t.passing * 0.20 + t.shooting * 0.20 + t.dribbling * 0.20 +
                t.defending * 0.10 + t.vision * 0.10 + t.finishing * 0.20)
        return round(score * 10, 2)

class ExperienceEngine:
    def calculate(self, player):
        years = min(player.experience.years * 2, 20)
        matches = min(player.experience.matches / 10, 40)
        training = player.experience.training_days * 8
        return years + matches + training

class OverallEngine:
    def calculate(self, player):
        physical = PhysicalEngine().calculate(player)
        technical = TechnicalEngine().calculate(player)
        experience = ExperienceEngine().calculate(player)
        overall = physical * 0.35 + technical * 0.45 + experience * 0.20
        return round(overall, 2)

POSITION_WEIGHTS = {
    "Football": {
        "Goalkeeper": {"defending": 0.35, "vision": 0.25, "agility": 0.20, "strength": 0.10, "passing": 0.10},
        "Center Back": {"defending": 0.35, "strength": 0.25, "speed": 0.10, "passing": 0.10, "endurance": 0.10, "vision": 0.10},
        "Right Back": {"speed": 0.25, "defending": 0.25, "passing": 0.20, "endurance": 0.15, "dribbling": 0.15},
        "Left Back": {"speed": 0.25, "defending": 0.25, "passing": 0.20, "endurance": 0.15, "dribbling": 0.15},
        "Defensive Midfielder": {"defending": 0.30, "passing": 0.25, "strength": 0.15, "vision": 0.15, "endurance": 0.15},
        "Central Midfielder": {"passing": 0.30, "vision": 0.25, "endurance": 0.20, "dribbling": 0.10, "defending": 0.10, "speed": 0.05},
        "Attacking Midfielder": {"passing": 0.25, "vision": 0.25, "dribbling": 0.20, "shooting": 0.15, "finishing": 0.10, "speed": 0.05},
        "Right Winger": {"speed": 0.25, "dribbling": 0.25, "passing": 0.15, "shooting": 0.15, "finishing": 0.10, "vision": 0.10},
        "Left Winger": {"speed": 0.25, "dribbling": 0.25, "passing": 0.15, "shooting": 0.15, "finishing": 0.10, "vision": 0.10},
        "Striker": {"shooting": 0.30, "finishing": 0.25, "speed": 0.20, "dribbling": 0.10, "passing": 0.10, "vision": 0.05},
        "Center Forward": {"shooting": 0.30, "finishing": 0.25, "speed": 0.20, "dribbling": 0.10, "passing": 0.10, "vision": 0.05}
    },
    "Basketball": {
        "Point Guard": {"passing": 0.35, "vision": 0.30, "dribbling": 0.20, "speed": 0.15},
        "Shooting Guard": {"shooting": 0.35, "dribbling": 0.20, "speed": 0.20, "passing": 0.15, "vision": 0.10},
        "Small Forward": {"speed": 0.20, "shooting": 0.20, "strength": 0.15, "dribbling": 0.15, "passing": 0.15, "defending": 0.15},
        "Power Forward": {"strength": 0.30, "defending": 0.25, "shooting": 0.15, "endurance": 0.15, "passing": 0.15},
        "Center": {"strength": 0.35, "defending": 0.30, "shooting": 0.10, "passing": 0.10, "endurance": 0.15}
    },
    "Handball": {
        "Goalkeeper": {"vision": 0.30, "agility": 0.25, "defending": 0.30, "strength": 0.15},
        "Left Wing": {"speed": 0.30, "shooting": 0.25, "dribbling": 0.20, "agility": 0.15, "passing": 0.10},
        "Right Wing": {"speed": 0.30, "shooting": 0.25, "dribbling": 0.20, "agility": 0.15, "passing": 0.10},
        "Pivot": {"strength": 0.35, "shooting": 0.25, "defending": 0.20, "passing": 0.20},
        "Center Back": {"passing": 0.30, "vision": 0.25, "shooting": 0.20, "dribbling": 0.15, "speed": 0.10},
        "Left Back": {"shooting": 0.30, "strength": 0.20, "speed": 0.20, "passing": 0.15, "vision": 0.15},
        "Right Back": {"shooting": 0.30, "strength": 0.20, "speed": 0.20, "passing": 0.15, "vision": 0.15}
    },
    "Volleyball": {
        "Setter": {"passing": 0.35, "vision": 0.30, "agility": 0.20, "speed": 0.15},
        "Outside Hitter": {"shooting": 0.30, "speed": 0.25, "agility": 0.20, "strength": 0.15, "passing": 0.10},
        "Opposite": {"shooting": 0.35, "strength": 0.25, "speed": 0.15, "agility": 0.15, "passing": 0.10},
        "Middle Blocker": {"strength": 0.35, "defending": 0.30, "agility": 0.20, "speed": 0.15},
        "Libero": {"defending": 0.35, "passing": 0.25, "agility": 0.20, "speed": 0.20}
    }
}

class PositionEngine:
    def calculate(self, player):
        sport_name = player.sport.value
        position = player.position
        
        if position not in POSITION_WEIGHTS.get(sport_name, {}):
            if sport_name == "Football":
                position = "Striker"
            elif sport_name == "Basketball":
                position = "Small Forward"
            elif sport_name == "Handball":
                position = "Left Back"
            elif sport_name == "Volleyball":
                position = "Outside Hitter"
        
        weights = POSITION_WEIGHTS[sport_name][position]
        total = 0
        details = {}
        for skill, weight in weights.items():
            if hasattr(player.physical, skill):
                value = getattr(player.physical, skill)
            else:
                value = getattr(player.technical, skill)
            contribution = value * 10 * weight
            total += contribution
            details[skill] = {"score": value, "weight": weight, "contribution": round(contribution, 2)}
        return {"position_score": round(total, 2), "details": details}

class GroqComparisonEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    
    def _format_player_data(self, player: Player) -> str:
        return f"""
Player: {player.name}
Sport: {player.sport.value}
Position: {player.position}
Age: {player.age}
Height: {player.height} cm
Weight: {player.weight} kg

Physical Skills:
- Speed: {player.physical.speed}/10
- Strength: {player.physical.strength}/10
- Endurance: {player.physical.endurance}/10
- Agility: {player.physical.agility}/10
- Flexibility: {player.physical.flexibility}/10

Technical Skills:
- Passing: {player.technical.passing}/10
- Shooting: {player.technical.shooting}/10
- Dribbling: {player.technical.dribbling}/10
- Defending: {player.technical.defending}/10
- Vision: {player.technical.vision}/10
- Finishing: {player.technical.finishing}/10

Experience:
- Years: {player.experience.years}
- Matches: {player.experience.matches}
- Training Days/Week: {player.experience.training_days}
- Level: {player.experience.level.value}
"""
    
    def _get_skills_comparison(self, player1: Player, player2: Player) -> Dict:
        p1_physical = player1.physical.__dict__
        p1_technical = player1.technical.__dict__
        p2_physical = player2.physical.__dict__
        p2_technical = player2.technical.__dict__
        
        comparison = {"physical": {}, "technical": {}}
        
        for skill in p1_physical:
            comparison["physical"][skill] = {
                "player1": p1_physical[skill],
                "player2": p2_physical[skill],
                "diff": round(p1_physical[skill] - p2_physical[skill], 2)
            }
        
        for skill in p1_technical:
            comparison["technical"][skill] = {
                "player1": p1_technical[skill],
                "player2": p2_technical[skill],
                "diff": round(p1_technical[skill] - p2_technical[skill], 2)
            }
        
        return comparison
    
    def compare(self, player1: Player, player2: Player) -> Dict:
        if player1.sport != player2.sport:
            return {
                "error": "Cannot compare players from different sports",
                "player1_sport": player1.sport.value,
                "player2_sport": player2.sport.value
            }
        
        overall_engine = OverallEngine()
        position_engine = PositionEngine()
        
        score1 = overall_engine.calculate(player1)
        score2 = overall_engine.calculate(player2)
        
        pos_score1 = position_engine.calculate(player1)["position_score"]
        pos_score2 = position_engine.calculate(player2)["position_score"]
        
        skills_comparison = self._get_skills_comparison(player1, player2)
        
        prompt = f"""
As a world-class sports analyst and talent scout with 20 years of experience, provide a comprehensive, objective, and strategic comparison between these two {player1.sport.value} players.

PLAYER 1 PROFILE
{self._format_player_data(player1)}

PLAYER 2 PROFILE
{self._format_player_data(player2)}

QUANTITATIVE METRICS
{player1.name}:
- Overall Score: {score1}/100 (Composite of Physical 35%, Technical 45%, Experience 20%)
- Position Score ({player1.position}): {pos_score1}/100 (Weighted for optimal position performance)

{player2.name}:
- Overall Score: {score2}/100
- Position Score ({player2.position}): {pos_score2}/100

DETAILED SKILL COMPARISON
Physical Skills (0-10 scale):
{chr(10).join([f"* {skill.capitalize()}: {player1.name} = {skills_comparison['physical'][skill]['player1']} | {player2.name} = {skills_comparison['physical'][skill]['player2']} | Difference: {skills_comparison['physical'][skill]['diff']}" for skill in skills_comparison['physical']])}

Technical Skills (0-10 scale):
{chr(10).join([f"* {skill.capitalize()}: {player1.name} = {skills_comparison['technical'][skill]['player1']} | {player2.name} = {skills_comparison['technical'][skill]['player2']} | Difference: {skills_comparison['technical'][skill]['diff']}" for skill in skills_comparison['technical']])}

Please provide a comprehensive strategic analysis that includes:

1. STRENGTHS ANALYSIS: Identify and explain the key advantages of each player, including specific skills that make them exceptional.

2. WEAKNESSES AND LIMITATIONS: Objectively assess areas where each player needs improvement, with actionable insights.

3. HEAD-TO-HEAD SKILL BREAKDOWN: For each skill category, explain which player has the edge and WHY. Include context about how these skills translate to game situations.

4. POSITION FIT AND TACTICAL VALUE: Evaluate how well each player fits their position and their tactical value to a team. Consider modern tactical trends.

5. DEVELOPMENTAL TRAJECTORY: Project the future potential and growth path for each player. Who has higher ceiling? Who has higher floor?

6. FINAL RECOMMENDATION: Provide a clear, evidence-based conclusion on which player would be the better acquisition for a competitive team, considering both immediate impact and long-term value.

Be precise, data-driven, and avoid generic statements. Use your expert knowledge to connect the numbers to real-game scenarios.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a world-class sports analyst and talent scout with expertise in multiple sports. Your analysis is always objective, data-driven, and actionable. You understand both the numbers and the intangible qualities that make great players."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2500
            )
            
            analysis = response.choices[0].message.content
            
            if score1 > score2:
                winner = player1.name
                loser = player2.name
                winner_score = score1
                loser_score = score2
            elif score2 > score1:
                winner = player2.name
                loser = player1.name
                winner_score = score2
                loser_score = score1
            else:
                winner = "Draw"
                loser = "Draw"
                winner_score = score1
                loser_score = score2
            
            diff = abs(score1 - score2)
            confidence = min(98, 45 + diff * 2.5)
            
            return {
                "player1": {
                    "name": player1.name,
                    "sport": player1.sport.value,
                    "position": player1.position,
                    "overall_score": score1,
                    "position_score": pos_score1
                },
                "player2": {
                    "name": player2.name,
                    "sport": player2.sport.value,
                    "position": player2.position,
                    "overall_score": score2,
                    "position_score": pos_score2
                },
                "skills_comparison": skills_comparison,
                "winner": winner,
                "loser": loser,
                "winner_score": winner_score,
                "loser_score": loser_score,
                "confidence": round(confidence, 1),
                "analysis": analysis,
                "score_diff": round(abs(score1 - score2), 2)
            }
            
        except Exception as e:
            return {
                "error": f"Error connecting to Groq API: {str(e)}",
                "player1": player1.name,
                "player2": player2.name
            }
    
    def compare_with_recommendations(self, player1: Player, player2: Player) -> str:
        result = self.compare(player1, player2)
        
        if "error" in result:
            return f"ERROR: {result['error']}"
        
        output = f"""
{'='*60}
PLAYER COMPARISON: {result['player1']['name']} vs {result['player2']['name']}
{'='*60}

SUMMARY RESULTS:
--------------------------------------------------------------------------------
Player                     | Overall Score | Position Score
--------------------------------------------------------------------------------
{result['player1']['name']:<25} | {result['player1']['overall_score']:>12} | {result['player1']['position_score']:>12}
{result['player2']['name']:<25} | {result['player2']['overall_score']:>12} | {result['player2']['position_score']:>12}
--------------------------------------------------------------------------------

WINNER: {result['winner']}
SCORE DIFFERENCE: {result['score_diff']} points
CONFIDENCE: {result['confidence']}%

{'='*60}
DETAILED ANALYSIS:
{result['analysis']}
{'='*60}
"""
        return output
    
    def generate_pdf_report(self, player1: Player, player2: Player, output_path: str = None):
        result = self.compare(player1, player2)
        
        if "error" in result:
            return None
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name1 = self._sanitize_filename(player1.name)
            clean_name2 = self._sanitize_filename(player2.name)
            output_path = os.path.join(OUTPUT_DIR, f"comparison_report_{clean_name1}_{clean_name2}_{timestamp}.pdf")
        
        doc = SimpleDocTemplate(output_path, pagesize=A4, 
                               rightMargin=72, leftMargin=72, 
                               topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12,
            spaceBefore=20
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        )
        
        story = []
        
        story.append(Paragraph(
            f"<b>Player Comparison Report</b><br/><font size='14'>{player1.name} vs {player2.name}</font>",
            title_style
        ))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            body_style
        ))
        story.append(Spacer(1, 20))
        
        summary_data = [
            ['Player', 'Sport', 'Position', 'Overall Score', 'Position Score'],
            [
                player1.name,
                player1.sport.value,
                player1.position,
                str(result['player1']['overall_score']),
                str(result['player1']['position_score'])
            ],
            [
                player2.name,
                player2.sport.value,
                player2.position,
                str(result['player2']['overall_score']),
                str(result['player2']['position_score'])
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*cm, 3*cm, 3.5*cm, 2.5*cm, 2.5*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        winner_text = result['winner']
        story.append(Paragraph(
            f"<b>WINNER:</b> {winner_text}  |  <b>Score Diff:</b> {result['score_diff']}  |  "
            f"<b>Confidence:</b> {result['confidence']}%",
            heading_style
        ))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("<b>Skills Comparison (0-10 scale)</b>", heading_style))
        
        physical_skills = result['skills_comparison']['physical']
        technical_skills = result['skills_comparison']['technical']
        
        story.append(Paragraph("<b>Physical Skills</b>", heading_style))
        phys_data = [['Skill', f'{player1.name}', f'{player2.name}', 'Difference']]
        for skill, values in physical_skills.items():
            phys_data.append([
                skill.capitalize(),
                str(values['player1']),
                str(values['player2']),
                f"{'+' if values['diff'] > 0 else ''}{values['diff']}"
            ])
        
        phys_table = Table(phys_data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        phys_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(phys_table)
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("<b>Technical Skills</b>", heading_style))
        tech_data = [['Skill', f'{player1.name}', f'{player2.name}', 'Difference']]
        for skill, values in technical_skills.items():
            tech_data.append([
                skill.capitalize(),
                str(values['player1']),
                str(values['player2']),
                f"{'+' if values['diff'] > 0 else ''}{values['diff']}"
            ])
        
        tech_table = Table(tech_data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(tech_table)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("<b>Detailed Analysis</b>", heading_style))
        story.append(PageBreak())
        
        analysis_lines = result['analysis'].split('\n')
        for line in analysis_lines:
            if line.strip():
                if re.match(r'^\d+\.|\*\*', line.strip()):
                    story.append(Paragraph(f"<b>{line}</b>", body_style))
                else:
                    story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 4))
        
        doc.build(story)
        return output_path
    
    def _sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = re.sub(r'[\s]+', '_', name)
        name = name.strip('_')
        return name[:50]

class PlayerComparisonApp:
    def __init__(self, db: PlayerDatabase):
        self.db = db
        self.comparison_engine = GroqComparisonEngine()
    
    def _display_players_with_details(self, players: List[Player], title: str = "Players"):
        """Display players with full details including sport and position"""
        print(f"\n{title}:")
        print("-" * 100)
        print(f"{'#':<4} {'Name':<30} {'Sport':<15} {'Position':<25} {'Age':<5} {'ID':<8}")
        print("-" * 100)
        for i, p in enumerate(players, 1):
            print(f"{i:<4} {p.name[:28]:<30} {p.sport.value:<15} {p.position[:23]:<25} {p.age:<5} {p.player_id:<8}")
        print("-" * 100)
    
    def _select_player_by_name(self, prompt: str = "Select a player") -> Optional[Player]:
        print(f"\n{prompt}")
        name = input("Enter player name (or part of name): ").strip()
        
        if not name:
            print("No name entered.")
            return None
        
        # First try exact match
        exact_matches = self.db.search_by_exact_name(name)
        if len(exact_matches) == 1:
            player = exact_matches[0]
            print(f"Selected: {player.name} ({player.sport.value}) - Position: {player.position} - ID: {player.player_id}")
            return player
        elif len(exact_matches) > 1:
            print(f"\nFound {len(exact_matches)} players with exact name '{name}':")
            self._display_players_with_details(exact_matches, "Exact Matches")
            return self._select_from_list(exact_matches)
        
        # If no exact match, try partial match
        partial_matches = self.db.search_by_name(name)
        if not partial_matches:
            print(f"No players found with name containing '{name}'")
            return None
        
        if len(partial_matches) == 1:
            player = partial_matches[0]
            print(f"Selected: {player.name} ({player.sport.value}) - Position: {player.position} - ID: {player.player_id}")
            return player
        
        print(f"\nFound {len(partial_matches)} players with name containing '{name}':")
        self._display_players_with_details(partial_matches, "Matching Players")
        return self._select_from_list(partial_matches)
    
    def _select_from_list(self, players: List[Player]) -> Optional[Player]:
        """Helper method to select a player from a list with multiple selection options"""
        while True:
            try:
                print("\nSelection options:")
                print("  - Enter a number (1-{}) to select by position in list".format(len(players)))
                print("  - Enter the exact full name to select")
                print("  - Enter the player ID to select")
                print("  - Enter 'q' to quit")
                
                choice = input("\nYour choice: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                # Try as number (position in list)
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(players):
                        return players[idx]
                    print(f"Invalid number. Choose between 1 and {len(players)}")
                    continue
                except ValueError:
                    pass
                
                # Try as player ID
                try:
                    player_id = int(choice)
                    for player in players:
                        if player.player_id == player_id:
                            return player
                    print(f"No player found with ID {player_id}")
                    continue
                except ValueError:
                    pass
                
                # Try as exact name
                exact_matches = [p for p in players if p.name.lower() == choice.lower()]
                if len(exact_matches) == 1:
                    return exact_matches[0]
                elif len(exact_matches) > 1:
                    print(f"Found {len(exact_matches)} players with exact name '{choice}':")
                    self._display_players_with_details(exact_matches, "Exact Matches")
                    return self._select_from_list(exact_matches)
                else:
                    print(f"No match found for '{choice}'. Please try again.")
                    continue
                    
            except Exception as e:
                print(f"Invalid input: {e}. Please try again.")
                continue
    
    def _get_player_by_selection(self, prompt: str = "Select a player") -> Optional[Player]:
        player = self._select_player_by_name(prompt)
        if not player:
            print("No player selected.")
        return player
    
    def _ensure_same_sport(self, player1: Player, player2: Player) -> bool:
        if player1.sport != player2.sport:
            print(f"\nCannot compare players from different sports:")
            print(f"   {player1.name}: {player1.sport.value}")
            print(f"   {player2.name}: {player2.sport.value}")
            print("   Please select players from the same sport.")
            return False
        return True
    
    def run_comparison(self):
        print("\n" + "="*60)
        print("PLAYER COMPARISON SYSTEM - Powered by AI")
        print("="*60)
        
        all_players = self.db.get_all_players()
        if not all_players:
            print("\nNo players in database.")
            return
        
        print(f"\nTotal players in database: {len(all_players)}")
        
        print("\n" + "-"*40)
        print("SELECT PLAYER 1")
        player1 = self._get_player_by_selection("Select Player 1")
        if not player1:
            print("Comparison cancelled.")
            return
        
        print("\n" + "-"*40)
        print("SELECT PLAYER 2")
        player2 = self._get_player_by_selection("Select Player 2")
        if not player2:
            print("Comparison cancelled.")
            return
        
        if player1.player_id == player2.player_id:
            print("Cannot compare a player with themselves. Please select a different player.")
            return
        
        if not self._ensure_same_sport(player1, player2):
            return
        
        print("\n" + "Processing data and generating analysis...")
        print("-" * 40)
        
        result = self.comparison_engine.compare_with_recommendations(player1, player2)
        print(result)
        
        print("\n" + "-"*40)
        print("Export Options:")
        print("1. Save as PDF (professional report)")
        print("2. Save as TXT")
        print("3. Skip export")
        
        choice = input("\nSelect export option (1-3): ").strip()
        
        if choice == '1':
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                clean_name1 = self.comparison_engine._sanitize_filename(player1.name)
                clean_name2 = self.comparison_engine._sanitize_filename(player2.name)
                filename = f"comparison_report_{clean_name1}_{clean_name2}_{timestamp}.pdf"
                pdf_path = os.path.join(OUTPUT_DIR, filename)
                
                print("\nGenerating PDF report...")
                self.comparison_engine.generate_pdf_report(player1, player2, pdf_path)
                print(f"PDF Report saved to: {pdf_path}")
            except Exception as e:
                print(f"Error generating PDF: {e}")
                print("Saving as TXT instead...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                clean_name1 = self.comparison_engine._sanitize_filename(player1.name)
                clean_name2 = self.comparison_engine._sanitize_filename(player2.name)
                filename = f"comparison_report_{clean_name1}_{clean_name2}_{timestamp}.txt"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"Report saved to: {filepath}")
                
        elif choice == '2':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name1 = self.comparison_engine._sanitize_filename(player1.name)
            clean_name2 = self.comparison_engine._sanitize_filename(player2.name)
            filename = f"comparison_report_{clean_name1}_{clean_name2}_{timestamp}.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Report saved to: {filepath}")
        else:
            print("Export skipped.")

if __name__ == "__main__":
    # Database initialization
    db = PlayerDatabase()

    # Load from knowledge file if exists
    db.load_from_knowledge_file("players.json")

    print(f"Total players in database: {len(db.get_all_players())}")

    if len(db.get_all_players()) > 0:
        try:
            app = PlayerComparisonApp(db)
            app.run_comparison()
        except ValueError as e:
            print(f"Error: {e}")
            print("Please make sure GROQ_API_KEY is set in your .env file")
    else:
        print("\nNo players loaded. Creating sample players for testing...")
    
        sample_players = [
            Player(
                player_id=0,
                name="Ahmed Hassan",
                sport=Sport.FOOTBALL,
                position="Striker",
                age=25,
                height=178.0,
                weight=72.0,
                physical=Physical(speed=8.5, strength=7.0, endurance=8.0, agility=7.5, flexibility=7.0),
                technical=Technical(passing=7.5, shooting=9.0, dribbling=8.0, defending=5.0, vision=7.0, finishing=9.5),
                experience=Experience(years=7, matches=150, training_days=5, level=Level.ADVANCED)
            ),
            Player(
                player_id=0,
                name="Ahmed Ibrahim",
                sport=Sport.FOOTBALL,
                position="Goalkeeper",
                age=22,
                height=188.0,
                weight=80.0,
                physical=Physical(speed=6.5, strength=8.0, endurance=7.0, agility=8.5, flexibility=8.0),
                technical=Technical(passing=6.0, shooting=4.0, dribbling=5.0, defending=9.0, vision=7.0, finishing=3.0),
                experience=Experience(years=4, matches=80, training_days=5, level=Level.BEGINNER)
            ),
            Player(
                player_id=0,
                name="Ahmed Mohammed",
                sport=Sport.BASKETBALL,
                position="Shooting Guard",
                age=26,
                height=193.0,
                weight=88.0,
                physical=Physical(speed=8.0, strength=8.5, endurance=8.0, agility=7.5, flexibility=7.5),
                technical=Technical(passing=8.0, shooting=9.0, dribbling=8.5, defending=7.5, vision=8.0, finishing=8.5),
                experience=Experience(years=8, matches=180, training_days=6, level=Level.ADVANCED)
            ),
            Player(
                player_id=0,
                name="Mohamed Ali",
                sport=Sport.FOOTBALL,
                position="Central Midfielder",
                age=27,
                height=182.0,
                weight=75.0,
                physical=Physical(speed=7.0, strength=8.0, endurance=9.0, agility=7.0, flexibility=7.5),
                technical=Technical(passing=9.0, shooting=7.5, dribbling=8.5, defending=7.0, vision=9.0, finishing=7.0),
                experience=Experience(years=9, matches=200, training_days=6, level=Level.ADVANCED)
            ),
            Player(
                player_id=0,
                name="Khaled Youssef",
                sport=Sport.BASKETBALL,
                position="Point Guard",
                age=24,
                height=185.0,
                weight=82.0,
                physical=Physical(speed=9.0, strength=7.5, endurance=8.5, agility=8.5, flexibility=8.0),
                technical=Technical(passing=9.5, shooting=8.0, dribbling=9.0, defending=7.0, vision=9.0, finishing=8.5),
                experience=Experience(years=6, matches=120, training_days=5, level=Level.INTERMEDIATE)
            )
        ]
    
        for player in sample_players:
            db.add_player(player)
    
        print(f"Added {len(sample_players)} sample players for testing.")
    
        try:
            app = PlayerComparisonApp(db)
            app.run_comparison()
        except ValueError as e:
            print(f"Error: {e}")
