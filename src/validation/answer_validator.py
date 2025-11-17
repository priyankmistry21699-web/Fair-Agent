"""
Answer Validation Layer for FAIR-Agent System

Validates agent responses for quality, consistency, and safety before delivery.
Provides automatic checks and corrections to boost faithfulness and safety metrics.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of answer validation"""
    is_valid: bool
    confidence_adjustment: float  # -0.3 to +0.1
    corrections: List[str]
    warnings: List[str]
    quality_score: float  # 0.0 to 1.0

class AnswerValidator:
    """
    Validates agent responses for quality and safety
    
    Performs 4 key validation checks:
    1. Evidence citation verification
    2. Numerical consistency checks  
    3. Medical/financial safety checks
    4. Response completeness validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Medical safety keywords requiring disclaimers
        self.medical_safety_keywords = [
            'treatment', 'medication', 'drug', 'dose', 'symptom', 'diagnosis',
            'therapy', 'surgery', 'prescription', 'condition', 'disease'
        ]
        
        # Financial safety keywords requiring disclaimers
        self.financial_safety_keywords = [
            'invest', 'stock', 'trade', 'buy', 'sell', 'portfolio',
            'recommendation', 'advice', 'should invest', 'guaranteed'
        ]
    
    def validate_response(
        self, 
        answer: str, 
        question: str, 
        domain: str,
        evidence_sources: List = None
    ) -> ValidationResult:
        """
        Validate response quality and safety
        
        Args:
            answer: The generated answer
            question: Original question
            domain: Domain (medical/finance/general)
            evidence_sources: Evidence sources used (if any)
            
        Returns:
            ValidationResult with validation status and adjustments
        """
        corrections = []
        warnings = []
        confidence_adjustment = 0.0
        quality_scores = []
        
        # Check 1: Evidence citation verification
        citation_score, citation_issues = self._validate_citations(answer, evidence_sources)
        quality_scores.append(citation_score)
        
        if citation_issues:
            warnings.extend(citation_issues)
            if citation_score < 0.5:
                confidence_adjustment -= 0.10  # Reduce confidence for poor citations
        
        # Check 2: Numerical consistency
        numerical_score, numerical_issues = self._validate_numerical_consistency(answer, question)
        quality_scores.append(numerical_score)
        
        if numerical_issues:
            warnings.extend(numerical_issues)
            if numerical_score < 0.6:
                confidence_adjustment -= 0.15  # Major penalty for numerical errors
        
        # Check 3: Domain-specific safety checks
        safety_score, safety_issues, safety_corrections = self._validate_domain_safety(
            answer, question, domain
        )
        quality_scores.append(safety_score)
        
        if safety_corrections:
            corrections.extend(safety_corrections)
        if safety_issues:
            warnings.extend(safety_issues)
        if safety_score < 0.7:
            confidence_adjustment -= 0.20  # Strong penalty for safety issues
        
        # Check 4: Response completeness
        completeness_score, completeness_issues = self._validate_completeness(answer, question)
        quality_scores.append(completeness_score)
        
        if completeness_issues:
            warnings.extend(completeness_issues)
            if completeness_score < 0.5:
                confidence_adjustment -= 0.08
        
        # Overall quality score
        overall_quality = sum(quality_scores) / len(quality_scores)
        
        # Determine if valid (must pass minimum thresholds)
        is_valid = (
            citation_score >= 0.4 and
            numerical_score >= 0.5 and
            safety_score >= 0.6 and
            completeness_score >= 0.4
        )
        
        # Small bonus for high quality
        if overall_quality > 0.85:
            confidence_adjustment += 0.05
        
        self.logger.info(
            f"Validation: quality={overall_quality:.2f}, "
            f"citation={citation_score:.2f}, numerical={numerical_score:.2f}, "
            f"safety={safety_score:.2f}, completeness={completeness_score:.2f}"
        )
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_adjustment=confidence_adjustment,
            corrections=corrections,
            warnings=warnings,
            quality_score=overall_quality
        )
    
    def _validate_citations(
        self, 
        answer: str, 
        evidence_sources: List
    ) -> Tuple[float, List[str]]:
        """
        Validate evidence citations in response
        
        Returns: (score, issues)
        """
        issues = []
        
        # Check if evidence sources were provided
        if not evidence_sources or len(evidence_sources) == 0:
            # No evidence provided - can't validate citations
            return 0.7, []  # Neutral score
        
        # Count citations in answer
        citation_pattern = r'\[Source \d+\]'
        citations = re.findall(citation_pattern, answer)
        citation_count = len(citations)
        
        # Expected: at least 1 citation per evidence source
        expected_min_citations = len(evidence_sources)
        
        if citation_count == 0:
            issues.append("⚠️ Response lacks evidence citations")
            return 0.2, issues
        
        if citation_count < expected_min_citations:
            issues.append(f"⚠️ Underutilized evidence ({citation_count}/{expected_min_citations} sources cited)")
            score = 0.5 + (citation_count / expected_min_citations) * 0.3
            return score, issues
        
        # Good citation usage
        if citation_count >= expected_min_citations:
            return 0.9, []
        
        return 0.7, issues
    
    def _validate_numerical_consistency(
        self, 
        answer: str, 
        question: str
    ) -> Tuple[float, List[str]]:
        """
        Validate numerical values for consistency
        
        Returns: (score, issues)
        """
        issues = []
        
        # Extract numbers from answer
        numbers = re.findall(r'\b\d+\.?\d*%?\b', answer)
        
        # If no numbers, can't validate
        if len(numbers) == 0:
            return 1.0, []
        
        # Check for common numerical issues
        # 1. Percentages over 100% (usually errors)
        invalid_percentages = [n for n in numbers if n.endswith('%') and float(n[:-1]) > 100]
        if invalid_percentages:
            issues.append(f"⚠️ Suspicious percentage values: {invalid_percentages}")
            return 0.4, issues
        
        # 2. Extreme values (very large or very small)
        try:
            numeric_values = [float(n.rstrip('%')) for n in numbers if not n.endswith('%')]
            if numeric_values:
                max_val = max(numeric_values)
                if max_val > 1000000:  # Over 1 million (suspicious for most contexts)
                    issues.append("⚠️ Extremely large numerical value detected")
                    return 0.6, issues
        except ValueError:
            pass
        
        # 3. Check for calculation mentions without results
        calc_keywords = ['calculate', 'compute', 'formula', 'equation']
        has_calc_keywords = any(kw in answer.lower() for kw in calc_keywords)
        
        if has_calc_keywords and len(numbers) < 2:
            issues.append("⚠️ Calculation mentioned but results not shown")
            return 0.5, issues
        
        # All checks passed
        return 0.95, []
    
    def _validate_domain_safety(
        self, 
        answer: str, 
        question: str, 
        domain: str
    ) -> Tuple[float, List[str], List[str]]:
        """
        Validate domain-specific safety requirements
        
        Returns: (score, issues, corrections)
        """
        issues = []
        corrections = []
        answer_lower = answer.lower()
        
        if domain == 'medical':
            return self._validate_medical_safety(answer, answer_lower, issues, corrections)
        elif domain == 'finance':
            return self._validate_financial_safety(answer, answer_lower, issues, corrections)
        else:
            return 1.0, [], []
    
    def _validate_medical_safety(
        self, 
        answer: str, 
        answer_lower: str,
        issues: List[str],
        corrections: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Validate medical response safety"""
        
        # Check for medical safety keywords
        has_medical_content = any(kw in answer_lower for kw in self.medical_safety_keywords)
        
        if not has_medical_content:
            return 1.0, issues, corrections
        
        # Required disclaimers for medical content
        required_phrases = [
            'consult', 'healthcare provider', 'medical professional', 
            'doctor', 'physician', 'professional advice'
        ]
        
        has_disclaimer = any(phrase in answer_lower for phrase in required_phrases)
        
        if not has_disclaimer:
            issues.append("⚠️ Medical response lacks professional consultation disclaimer")
            corrections.append(
                "ADD DISCLAIMER: This information is for educational purposes only. "
                "Always consult a qualified healthcare provider for medical advice."
            )
            return 0.3, issues, corrections
        
        # Check for absolute/definitive language (dangerous in medical context)
        absolute_terms = ['always', 'never', 'definitely', 'guaranteed', 'cure']
        has_absolute = any(term in answer_lower for term in absolute_terms)
        
        if has_absolute:
            issues.append("⚠️ Medical response uses absolute language (risky)")
            return 0.7, issues, corrections
        
        return 0.95, issues, corrections
    
    def _validate_financial_safety(
        self, 
        answer: str, 
        answer_lower: str,
        issues: List[str],
        corrections: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Validate financial response safety"""
        
        # Check for financial safety keywords
        has_financial_advice = any(kw in answer_lower for kw in self.financial_safety_keywords)
        
        if not has_financial_advice:
            return 1.0, issues, corrections
        
        # Check for investment advice disclaimers
        disclaimer_phrases = [
            'not financial advice', 'consult', 'financial advisor', 
            'professional advice', 'past performance', 'risk'
        ]
        
        has_disclaimer = any(phrase in answer_lower for phrase in disclaimer_phrases)
        
        if not has_disclaimer:
            issues.append("⚠️ Financial advice lacks appropriate disclaimers")
            corrections.append(
                "ADD DISCLAIMER: This is educational information, not financial advice. "
                "Consult a qualified financial advisor before making investment decisions."
            )
            return 0.4, issues, corrections
        
        # Check for guaranteed returns language (major red flag)
        dangerous_terms = ['guaranteed profit', 'guaranteed return', 'no risk', 'cant lose']
        has_dangerous = any(term in answer_lower for term in dangerous_terms)
        
        if has_dangerous:
            issues.append("⚠️ CRITICAL: Financial response makes dangerous guarantee claims")
            corrections.append("REMOVE: Guaranteed return claims are false and misleading")
            return 0.2, issues, corrections
        
        return 0.95, issues, corrections
    
    def _validate_completeness(
        self, 
        answer: str, 
        question: str
    ) -> Tuple[float, List[str]]:
        """
        Validate response completeness
        
        Returns: (score, issues)
        """
        issues = []
        
        # Check minimum length
        if len(answer) < 50:
            issues.append("⚠️ Response too short")
            return 0.3, issues
        
        # Check for incomplete sentences
        if answer.rstrip().endswith('...') or answer.rstrip().endswith(','):
            issues.append("⚠️ Response appears incomplete (ends with ellipsis or comma)")
            return 0.5, issues
        
        # Check if question keywords are addressed
        question_lower = question.lower()
        question_words = set(re.findall(r'\b\w{4,}\b', question_lower))  # 4+ letter words
        answer_lower = answer.lower()
        
        # Remove common stop words
        stop_words = {'what', 'when', 'where', 'which', 'should', 'would', 'could', 'does', 'have'}
        question_words = question_words - stop_words
        
        if question_words:
            addressed_words = sum(1 for word in question_words if word in answer_lower)
            coverage_ratio = addressed_words / len(question_words)
            
            if coverage_ratio < 0.3:
                issues.append("⚠️ Response doesn't address key question terms")
                return 0.4, issues
            
            if coverage_ratio < 0.5:
                issues.append("⚠️ Response partially addresses question")
                return 0.7, issues
        
        # All completeness checks passed
        return 0.95, []
    
    def apply_corrections(
        self, 
        answer: str, 
        validation_result: ValidationResult
    ) -> str:
        """
        Apply automatic corrections to improve answer quality
        
        Args:
            answer: Original answer
            validation_result: Validation result with corrections
            
        Returns:
            Corrected answer
        """
        corrected_answer = answer
        
        # Apply any automatic corrections
        for correction in validation_result.corrections:
            if correction.startswith("ADD DISCLAIMER:"):
                disclaimer = correction.replace("ADD DISCLAIMER:", "").strip()
                # Add disclaimer at the end if not already present
                if disclaimer.lower() not in corrected_answer.lower():
                    corrected_answer += f"\n\n**⚠️ Important:** {disclaimer}"
        
        return corrected_answer
