import time
from datetime import datetime
import threading

class SimpleProctorSystem:
    def __init__(self):
        self.is_monitoring = False
        self.suspicious_activities = []
        self.monitoring_data = {
            'start_time': None,
            'end_time': None,
            'tab_switches': 0,
            'copy_attempts': 0,
            'inactivity_periods': 0
        }
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start the proctor monitoring system"""
        self.is_monitoring = True
        self.monitoring_data['start_time'] = datetime.now()
        self.suspicious_activities = []
        
        def monitor():
            while self.is_monitoring:
                # Simulate monitoring activities
                time.sleep(5)  # Check every 5 seconds
                
                if not self.is_monitoring:
                    break
                
                # Simulate random suspicious activities (in real implementation, 
                # this would use browser events via JavaScript)
                if not self.suspicious_activities or len(self.suspicious_activities) < 10:
                    activities = [
                        "Possible looking away from screen",
                        "Background noise detected",
                        "Unusual typing pattern",
                        "Possible second screen usage",
                        "Inactivity period detected"
                    ]
                    
                    # Add a random activity occasionally
                    if self.is_monitoring and not self.suspicious_activities:
                        activity = {
                            'activity': "Monitoring started",
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'severity': 'info'
                        }
                        self.suspicious_activities.append(activity)
                    
                    if self.is_monitoring and len(self.suspicious_activities) < 5:
                        import random
                        if random.random() < 0.3:  # 30% chance of activity
                            activity = {
                                'activity': random.choice(activities),
                                'timestamp': datetime.now().strftime("%H:%M:%S"),
                                'severity': random.choice(['low', 'medium'])
                            }
                            self.suspicious_activities.append(activity)
            
            self.monitoring_data['end_time'] = datetime.now()
        
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the proctor monitoring system"""
        self.is_monitoring = False
        self.monitoring_data['end_time'] = datetime.now()
    
    def add_suspicious_activity(self, activity, severity='medium'):
        """Manually add a suspicious activity"""
        activity_record = {
            'activity': activity,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'severity': severity
        }
        self.suspicious_activities.append(activity_record)
    
    def get_monitoring_report(self):
        """Generate a monitoring report"""
        duration = None
        if self.monitoring_data['start_time'] and self.monitoring_data['end_time']:
            duration = (self.monitoring_data['end_time'] - self.monitoring_data['start_time']).total_seconds()
        
        return {
            'duration_seconds': duration,
            'suspicious_activities': self.suspicious_activities,
            'tab_switches': self.monitoring_data['tab_switches'],
            'copy_attempts': self.monitoring_data['copy_attempts'],
            'summary': self.generate_summary()
        }
    
    def generate_summary(self):
        if not self.suspicious_activities:
            return "No suspicious activities detected. Test was conducted properly."
        
        return f"Detected {len(self.suspicious_activities)} suspicious activities during the test."

# Singleton instance
proctor_system = SimpleProctorSystem()