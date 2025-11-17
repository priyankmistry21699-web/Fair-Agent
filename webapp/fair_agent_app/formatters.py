"""
Response formatting utilities for FAIR-Agent Web Application
"""

import re


class ResponseFormatter:
    """Utility class to format FAIR-Agent responses for web display"""
    
    @staticmethod
    def format_response_html(text: str) -> str:
        """
        Convert raw FAIR-Agent response text to clean HTML formatting with Times New Roman
        """
        if not text:
            return '<p style="font-family: \'Times New Roman\', Times, serif;">No response available</p>'
        
        # Clean up the text first
        formatted = text.strip()
        
        # Handle markdown links [text](url) - MUST BE DONE BEFORE bold/italic to preserve []
        formatted = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color: #0066cc; text-decoration: underline;">\1</a>', formatted)
        
        # Handle bold text with ** (if present)
        formatted = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', formatted)
        
        # Handle italic text with * (if present)
        formatted = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', formatted)
        
        # Split into lines for processing
        lines = formatted.split('\n')
        html_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Main introduction paragraph
            if 'Finance is the field that deals with' in line:
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; font-size: 16px; margin-bottom: 20px; font-weight: bold;">{line}</p>')
            
            # Numbered sections (1. Personal Finance:, 2. Corporate Finance:, etc.)
            elif re.match(r'^\d+\.\s+[A-Z].*?:', line):
                html_lines.append(f'<h3 style="font-family: \'Times New Roman\', Times, serif; margin-top: 25px; margin-bottom: 15px; color: #000; font-weight: bold;">{line}</h3>')
            
            # Key Financial Principles header (without number)
            elif line.endswith(':') and ('Key' in line or 'Principles' in line or 'Process' in line):
                html_lines.append(f'<h3 style="font-family: \'Times New Roman\', Times, serif; margin-top: 25px; margin-bottom: 15px; color: #000; font-weight: bold;">{line}</h3>')
            
            # Bullet points with dashes
            elif line.startswith('- '):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin-left: 30px; margin-bottom: 8px;">• {line[2:].strip()}</p>')
            
            # Bullet points with bullets
            elif line.startswith('• '):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin-left: 30px; margin-bottom: 8px;">{line}</p>')
            
            # Emergency Notice
            elif line.startswith('EMERGENCY NOTICE:'):
                html_lines.append(f'<div style="border: 2px solid #000; padding: 15px; margin: 20px 0; font-family: \'Times New Roman\', Times, serif;"><strong>Emergency Notice</strong><br>{line[17:].strip()}</div>')
            
            # Financial Disclaimer
            elif line.startswith('FINANCIAL DISCLAIMER:'):
                html_lines.append(f'<div style="border: 2px solid #000; padding: 15px; margin: 20px 0; font-family: \'Times New Roman\', Times, serif;"><strong>Financial Disclaimer</strong><br>{line[21:].strip()}</div>')
            
            # My Reasoning Process header
            elif line == 'My Reasoning Process:':
                html_lines.append('<div style="border: 2px solid #000; padding: 15px; margin: 20px 0; font-family: \'Times New Roman\', Times, serif;"><strong>Reasoning Process</strong></div>')
            
            # Steps
            elif line.startswith('Step '):
                if ':' in line:
                    step_part, content = line.split(':', 1)
                    html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 15px 0;"><strong>{step_part}:</strong> {content.strip()}</p>')
                else:
                    html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 15px 0;"><strong>{line}</strong></p>')
            
            # Supporting information
            elif line.startswith('Supporting information:'):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 10px 0; margin-left: 20px; font-style: italic;">{line}</p>')
            
            # Final Analysis
            elif line.startswith('Final Analysis:'):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 20px 0; font-weight: bold;">{line}</p>')
            
            # Confidence and scores
            elif any(keyword in line for keyword in ['Confidence:', 'Score:']):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 10px 0; font-weight: bold;">{line}</p>')
            
            # Additional Information from Trusted Sources
            elif line == 'Additional Information from Trusted Sources':
                html_lines.append('<div style="border: 2px solid #000; padding: 15px; margin: 20px 0; font-family: \'Times New Roman\', Times, serif;"><strong>Additional Information from Trusted Sources</strong></div>')
            
            # Source information with reliability
            elif line.startswith('Source ') and 'Reliability:' in line:
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 15px 0; font-weight: bold;">{line}</p>')
            
            # Source references
            elif line.startswith('Source:'):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 5px 0; margin-left: 20px; font-style: italic;">{line}</p>')
            
            # Information Quality
            elif line.startswith('Information Quality:'):
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; margin: 15px 0; font-weight: bold;">{line}</p>')
            
            # Standalone numbers (like "3." or "4.")
            elif line in ['3.', '4.', '5.', '6.']:
                # Skip these standalone numbers as they seem to be formatting artifacts
                continue
            
            # Conclusion paragraph (the final summary)
            elif 'Finance helps individuals, businesses, and governments' in line:
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; font-size: 16px; margin: 20px 0; font-weight: bold;">{line}</p>')
            
            # Regular paragraphs
            else:
                html_lines.append(f'<p style="font-family: \'Times New Roman\', Times, serif; line-height: 1.6; margin: 10px 0;">{line}</p>')
        
        return '\n'.join(html_lines)
