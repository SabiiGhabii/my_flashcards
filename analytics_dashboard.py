#!/usr/bin/env python3
"""
Advanced Analytics Dashboard

This module provides comprehensive analytics and insights for:
- Learning progress tracking
- Performance analysis
- Content effectiveness measurement
- Retention prediction
- Study optimization recommendations
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.figure import Figure
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.live import Live
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


@dataclass
class LearningMetrics:
    """Learning performance metrics"""
    total_cards: int
    cards_mastered: int
    cards_learning: int
    cards_new: int
    average_retention: float
    study_streak: int
    total_study_time: float
    concepts_covered: int


@dataclass
class ContentAnalytics:
    """Content effectiveness analytics"""
    source_type: str
    total_cards_generated: int
    card_type_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    tag_frequency: Dict[str, int]
    processing_time: float
    success_rate: float


@dataclass
class PerformanceTrend:
    """Performance trend data"""
    date: datetime
    cards_reviewed: int
    accuracy: float
    response_time: float
    retention_rate: float


class LearningAnalytics:
    """Advanced learning analytics engine"""
    
    def __init__(self, data_dir: str = "analytics_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data storage
        self.study_sessions = []
        self.card_performance = {}
        self.content_analytics = []
        self.learning_objectives = {}
    
    def track_study_session(self, session_data: Dict[str, Any]):
        """Track a study session"""
        session = {
            "timestamp": datetime.now().isoformat(),
            "cards_reviewed": session_data.get("cards_reviewed", 0),
            "correct_answers": session_data.get("correct_answers", 0),
            "total_time": session_data.get("total_time", 0),
            "difficulty_level": session_data.get("difficulty_level", "intermediate"),
            "content_source": session_data.get("content_source", "unknown"),
            "card_types": session_data.get("card_types", [])
        }
        
        self.study_sessions.append(session)
        self._save_session_data(session)
    
    def analyze_learning_progress(self, user_id: str = "default") -> LearningMetrics:
        """Analyze overall learning progress"""
        sessions = self._load_user_sessions(user_id)
        
        if not sessions:
            return LearningMetrics(0, 0, 0, 0, 0.0, 0, 0.0, 0)
        
        # Calculate metrics
        total_cards = sum(s.get("cards_reviewed", 0) for s in sessions)
        total_correct = sum(s.get("correct_answers", 0) for s in sessions)
        total_time = sum(s.get("total_time", 0) for s in sessions)
        
        # Estimate mastery levels (simplified)
        cards_mastered = int(total_correct * 0.7)  # Cards with high retention
        cards_learning = int(total_correct * 0.3)  # Cards being learned
        cards_new = max(0, total_cards - total_correct)
        
        average_retention = total_correct / total_cards if total_cards > 0 else 0
        study_streak = self._calculate_study_streak(sessions)
        concepts_covered = len(set(s.get("content_source", "") for s in sessions))
        
        return LearningMetrics(
            total_cards=total_cards,
            cards_mastered=cards_mastered,
            cards_learning=cards_learning,
            cards_new=cards_new,
            average_retention=average_retention,
            study_streak=study_streak,
            total_study_time=total_time,
            concepts_covered=concepts_covered
        )
    
    def generate_performance_insights(self, user_id: str = "default") -> Dict[str, Any]:
        """Generate detailed performance insights"""
        sessions = self._load_user_sessions(user_id)
        
        if not sessions:
            return {"error": "No session data available"}
        
        # Performance trends
        trends = self._calculate_performance_trends(sessions)
        
        # Difficulty analysis
        difficulty_performance = self._analyze_difficulty_performance(sessions)
        
        # Content type effectiveness
        content_effectiveness = self._analyze_content_effectiveness(sessions)
        
        # Time-based patterns
        time_patterns = self._analyze_time_patterns(sessions)
        
        # Recommendations
        recommendations = self._generate_recommendations(sessions, trends)
        
        return {
            "performance_trends": trends,
            "difficulty_analysis": difficulty_performance,
            "content_effectiveness": content_effectiveness,
            "time_patterns": time_patterns,
            "recommendations": recommendations,
            "last_updated": datetime.now().isoformat()
        }
    
    def predict_retention(self, card_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Predict retention probability for a specific card"""
        card_history = self._get_card_history(card_id, user_id)
        
        if not card_history:
            return {"retention_probability": 0.5, "confidence": "low"}
        
        # Simple retention model (would use ML in production)
        recent_performance = card_history[-5:]  # Last 5 reviews
        accuracy = sum(r.get("correct", 0) for r in recent_performance) / len(recent_performance)
        
        # Factor in time since last review
        last_review = datetime.fromisoformat(card_history[-1]["timestamp"])
        days_since = (datetime.now() - last_review).days
        
        # Forgetting curve approximation
        retention_probability = accuracy * np.exp(-days_since / 30)  # 30-day half-life
        
        confidence = "high" if len(card_history) >= 5 else "medium" if len(card_history) >= 2 else "low"
        
        return {
            "retention_probability": min(1.0, max(0.0, retention_probability)),
            "confidence": confidence,
            "days_since_review": days_since,
            "review_count": len(card_history),
            "average_accuracy": accuracy
        }
    
    def optimize_study_schedule(self, user_id: str = "default") -> Dict[str, Any]:
        """Generate optimized study schedule recommendations"""
        metrics = self.analyze_learning_progress(user_id)
        insights = self.generate_performance_insights(user_id)
        
        # Analyze current performance
        current_retention = metrics.average_retention
        study_consistency = insights.get("time_patterns", {}).get("consistency_score", 0.5)
        
        # Generate recommendations
        recommendations = []
        
        if current_retention < 0.7:
            recommendations.append({
                "type": "retention_improvement",
                "priority": "high",
                "suggestion": "Focus on reviewing cards with low retention rates",
                "action": "Increase review frequency for difficult cards"
            })
        
        if study_consistency < 0.6:
            recommendations.append({
                "type": "consistency",
                "priority": "medium",
                "suggestion": "Establish a more consistent study schedule",
                "action": "Set daily study reminders and shorter, regular sessions"
            })
        
        if metrics.cards_new > metrics.cards_learning * 2:
            recommendations.append({
                "type": "pacing",
                "priority": "medium",
                "suggestion": "Reduce new card introduction rate",
                "action": "Focus on mastering current cards before adding new ones"
            })
        
        # Optimal study times based on performance patterns
        time_patterns = insights.get("time_patterns", {})
        best_times = time_patterns.get("peak_performance_hours", ["09:00", "14:00", "19:00"])
        
        return {
            "recommendations": recommendations,
            "optimal_study_times": best_times,
            "suggested_session_length": self._calculate_optimal_session_length(insights),
            "priority_cards": self._identify_priority_cards(user_id),
            "weekly_schedule": self._generate_weekly_schedule(metrics, insights)
        }
    
    def create_visual_dashboard(self, user_id: str = "default") -> Dict[str, Any]:
        """Create visual analytics dashboard"""
        if not HAS_PLOTTING:
            return {"error": "Plotting libraries not available"}
        
        metrics = self.analyze_learning_progress(user_id)
        insights = self.generate_performance_insights(user_id)
        
        # Create visualizations
        visualizations = {}
        
        # Progress overview
        visualizations["progress_chart"] = self._create_progress_chart(metrics)
        
        # Performance trends
        visualizations["performance_trends"] = self._create_performance_trends_chart(insights)
        
        # Content effectiveness
        visualizations["content_effectiveness"] = self._create_content_effectiveness_chart(insights)
        
        # Retention heatmap
        visualizations["retention_heatmap"] = self._create_retention_heatmap(user_id)
        
        return visualizations
    
    def export_analytics_report(self, user_id: str = "default", 
                              format: str = "json") -> str:
        """Export comprehensive analytics report"""
        report_data = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "learning_metrics": self.analyze_learning_progress(user_id).__dict__,
            "performance_insights": self.generate_performance_insights(user_id),
            "study_optimization": self.optimize_study_schedule(user_id),
            "summary": self._generate_summary_report(user_id)
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{user_id}_{timestamp}.{format}"
        filepath = self.data_dir / filename
        
        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        elif format == "csv":
            # Convert to DataFrame and save as CSV
            df = pd.json_normalize(report_data)
            df.to_csv(filepath, index=False)
        
        return str(filepath)
    
    def _calculate_study_streak(self, sessions: List[Dict[str, Any]]) -> int:
        """Calculate current study streak in days"""
        if not sessions:
            return 0
        
        # Sort sessions by date
        sorted_sessions = sorted(sessions, key=lambda x: x["timestamp"], reverse=True)
        
        streak = 0
        current_date = datetime.now().date()
        
        for session in sorted_sessions:
            session_date = datetime.fromisoformat(session["timestamp"]).date()
            
            if session_date == current_date or session_date == current_date - timedelta(days=streak):
                if session_date == current_date - timedelta(days=streak):
                    streak += 1
                current_date = session_date
            else:
                break
        
        return streak
    
    def _calculate_performance_trends(self, sessions: List[Dict[str, Any]]) -> List[PerformanceTrend]:
        """Calculate performance trends over time"""
        trends = []
        
        # Group sessions by day
        daily_sessions = {}
        for session in sessions:
            date = datetime.fromisoformat(session["timestamp"]).date()
            if date not in daily_sessions:
                daily_sessions[date] = []
            daily_sessions[date].append(session)
        
        # Calculate daily metrics
        for date, day_sessions in sorted(daily_sessions.items()):
            total_cards = sum(s.get("cards_reviewed", 0) for s in day_sessions)
            total_correct = sum(s.get("correct_answers", 0) for s in day_sessions)
            total_time = sum(s.get("total_time", 0) for s in day_sessions)
            
            accuracy = total_correct / total_cards if total_cards > 0 else 0
            avg_response_time = total_time / total_cards if total_cards > 0 else 0
            
            trends.append(PerformanceTrend(
                date=datetime.combine(date, datetime.min.time()),
                cards_reviewed=total_cards,
                accuracy=accuracy,
                response_time=avg_response_time,
                retention_rate=accuracy  # Simplified
            ))
        
        return trends
    
    def _analyze_difficulty_performance(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by difficulty level"""
        difficulty_stats = {}
        
        for session in sessions:
            difficulty = session.get("difficulty_level", "intermediate")
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"total": 0, "correct": 0}
            
            difficulty_stats[difficulty]["total"] += session.get("cards_reviewed", 0)
            difficulty_stats[difficulty]["correct"] += session.get("correct_answers", 0)
        
        # Calculate accuracy for each difficulty
        for difficulty, stats in difficulty_stats.items():
            stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        
        return difficulty_stats
    
    def _analyze_content_effectiveness(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze effectiveness of different content types"""
        content_stats = {}
        
        for session in sessions:
            source = session.get("content_source", "unknown")
            if source not in content_stats:
                content_stats[source] = {"sessions": 0, "total_cards": 0, "total_correct": 0}
            
            content_stats[source]["sessions"] += 1
            content_stats[source]["total_cards"] += session.get("cards_reviewed", 0)
            content_stats[source]["total_correct"] += session.get("correct_answers", 0)
        
        # Calculate effectiveness metrics
        for source, stats in content_stats.items():
            stats["accuracy"] = stats["total_correct"] / stats["total_cards"] if stats["total_cards"] > 0 else 0
            stats["cards_per_session"] = stats["total_cards"] / stats["sessions"] if stats["sessions"] > 0 else 0
        
        return content_stats
    
    def _analyze_time_patterns(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze study time patterns"""
        hourly_performance = {}
        daily_consistency = {}
        
        for session in sessions:
            timestamp = datetime.fromisoformat(session["timestamp"])
            hour = timestamp.hour
            day = timestamp.strftime("%A")
            
            # Hourly patterns
            if hour not in hourly_performance:
                hourly_performance[hour] = {"sessions": 0, "total_accuracy": 0}
            
            accuracy = session.get("correct_answers", 0) / max(1, session.get("cards_reviewed", 1))
            hourly_performance[hour]["sessions"] += 1
            hourly_performance[hour]["total_accuracy"] += accuracy
        
        # Calculate average accuracy by hour
        for hour, stats in hourly_performance.items():
            stats["avg_accuracy"] = stats["total_accuracy"] / stats["sessions"]
        
        # Find peak performance hours
        peak_hours = sorted(hourly_performance.items(), 
                          key=lambda x: x[1]["avg_accuracy"], reverse=True)[:3]
        peak_performance_hours = [f"{hour:02d}:00" for hour, _ in peak_hours]
        
        return {
            "hourly_performance": hourly_performance,
            "peak_performance_hours": peak_performance_hours,
            "consistency_score": self._calculate_consistency_score(sessions)
        }
    
    def _calculate_consistency_score(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate study consistency score"""
        if len(sessions) < 7:
            return 0.5  # Not enough data
        
        # Calculate days with study sessions
        study_days = set()
        for session in sessions:
            date = datetime.fromisoformat(session["timestamp"]).date()
            study_days.add(date)
        
        # Calculate consistency over last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        days_in_period = (end_date - start_date).days
        study_days_in_period = len([d for d in study_days if start_date <= d <= end_date])
        
        return study_days_in_period / days_in_period
    
    def _generate_recommendations(self, sessions: List[Dict[str, Any]], 
                                trends: List[PerformanceTrend]) -> List[Dict[str, Any]]:
        """Generate personalized study recommendations"""
        recommendations = []
        
        if not trends:
            return recommendations
        
        # Analyze recent performance
        recent_trends = trends[-7:]  # Last 7 days
        if recent_trends:
            avg_accuracy = sum(t.retention_rate for t in recent_trends) / len(recent_trends)
            
            if avg_accuracy < 0.7:
                recommendations.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "Improve Retention Rate",
                    "description": "Your recent accuracy is below optimal. Consider reviewing cards more frequently.",
                    "action": "Increase review frequency for difficult cards"
                })
        
        return recommendations
    
    def _save_session_data(self, session: Dict[str, Any]):
        """Save session data to file"""
        sessions_file = self.data_dir / "study_sessions.jsonl"
        with open(sessions_file, 'a') as f:
            f.write(json.dumps(session) + '\n')
    
    def _load_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Load user session data"""
        sessions_file = self.data_dir / "study_sessions.jsonl"
        if not sessions_file.exists():
            return []
        
        sessions = []
        with open(sessions_file, 'r') as f:
            for line in f:
                try:
                    session = json.loads(line.strip())
                    # Filter by user_id if needed
                    sessions.append(session)
                except json.JSONDecodeError:
                    continue
        
        return sessions
    
    def _get_card_history(self, card_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get review history for a specific card"""
        # Placeholder - would load from card-specific storage
        return []
    
    def _calculate_optimal_session_length(self, insights: Dict[str, Any]) -> int:
        """Calculate optimal study session length in minutes"""
        # Based on performance patterns and attention span
        return 25  # Default Pomodoro technique
    
    def _identify_priority_cards(self, user_id: str) -> List[str]:
        """Identify cards that need priority review"""
        # Placeholder - would analyze card performance
        return []
    
    def _generate_weekly_schedule(self, metrics: LearningMetrics, 
                                insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized weekly study schedule"""
        return {
            "monday": {"focus": "new_cards", "duration": 30},
            "tuesday": {"focus": "review", "duration": 25},
            "wednesday": {"focus": "difficult_cards", "duration": 35},
            "thursday": {"focus": "review", "duration": 25},
            "friday": {"focus": "mixed", "duration": 30},
            "saturday": {"focus": "comprehensive_review", "duration": 45},
            "sunday": {"focus": "light_review", "duration": 20}
        }
    
    def _create_progress_chart(self, metrics: LearningMetrics) -> str:
        """Create progress visualization"""
        # Placeholder - would create actual chart
        return "progress_chart.png"
    
    def _create_performance_trends_chart(self, insights: Dict[str, Any]) -> str:
        """Create performance trends visualization"""
        return "performance_trends.png"
    
    def _create_content_effectiveness_chart(self, insights: Dict[str, Any]) -> str:
        """Create content effectiveness visualization"""
        return "content_effectiveness.png"
    
    def _create_retention_heatmap(self, user_id: str) -> str:
        """Create retention heatmap"""
        return "retention_heatmap.png"
    
    def _generate_summary_report(self, user_id: str) -> Dict[str, Any]:
        """Generate summary report"""
        metrics = self.analyze_learning_progress(user_id)
        
        return {
            "overall_progress": "good" if metrics.average_retention > 0.7 else "needs_improvement",
            "study_consistency": "excellent" if metrics.study_streak > 7 else "good" if metrics.study_streak > 3 else "needs_improvement",
            "key_achievements": [
                f"Mastered {metrics.cards_mastered} cards",
                f"Maintained {metrics.study_streak}-day study streak",
                f"Covered {metrics.concepts_covered} different concepts"
            ],
            "areas_for_improvement": [
                "Increase review frequency for difficult cards",
                "Maintain consistent daily study schedule",
                "Focus on long-term retention strategies"
            ]
        }


# Factory function
def create_analytics_dashboard(data_dir: str = "analytics_data") -> LearningAnalytics:
    """Create analytics dashboard instance"""
    return LearningAnalytics(data_dir)
