"""Core data types: prediction logs and their summary statistics.

A prediction log is the audit unit. Every record carries the system's
stated confidence, whether the system abstained on the case, and the
would-be outcome (whether the system's answer was, or would have been,
correct). Would-be outcomes for abstained cases are available in the
settings this tool audits: benchmark replays, internal evaluation runs
and regulatory audits where the full scoring run was logged before the
abstention decision was applied.
"""

import json


class Record(object):
    """One logged prediction: confidence, abstain flag, outcome."""

    __slots__ = ("confidence", "abstained", "correct")

    def __init__(self, confidence, abstained, correct):
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must lie in [0, 1]")
        self.confidence = confidence
        self.abstained = bool(abstained)
        self.correct = bool(correct)

    def __eq__(self, other):
        if not isinstance(other, Record):
            return NotImplemented
        return (self.confidence == other.confidence
                and self.abstained == other.abstained
                and self.correct == other.correct)

    def __repr__(self):
        return "Record(confidence=%.4f, abstained=%r, correct=%r)" % (
            self.confidence, self.abstained, self.correct)

    def to_dict(self):
        return {"confidence": self.confidence,
                "abstained": self.abstained,
                "correct": self.correct}

    @classmethod
    def from_dict(cls, payload):
        return cls(payload["confidence"], payload["abstained"],
                   payload["correct"])


class PredictionLog(object):
    """A full prediction log plus the metadata of the run that made it."""

    def __init__(self, records, meta=None):
        records = list(records)
        if not records:
            raise ValueError("a prediction log needs at least one record")
        self.records = records
        self.meta = dict(meta or {})

    def __len__(self):
        return len(self.records)

    @property
    def n(self):
        return len(self.records)

    @property
    def n_abstained(self):
        return sum(1 for r in self.records if r.abstained)

    @property
    def n_answered(self):
        return self.n - self.n_abstained

    @property
    def coverage(self):
        """Fraction of cases the system chose to answer."""
        return self.n_answered / float(self.n)

    def reported_accuracy(self):
        """Accuracy over answered cases: the number the vendor reports."""
        answered = [r for r in self.records if not r.abstained]
        if not answered:
            return None
        return sum(1 for r in answered if r.correct) / float(len(answered))

    def overall_accuracy(self):
        """Accuracy over all cases, using would-be outcomes throughout."""
        return sum(1 for r in self.records if r.correct) / float(self.n)

    def abstained_error_rate(self):
        """Share of abstained cases that would have been errors."""
        abstained = [r for r in self.records if r.abstained]
        if not abstained:
            return None
        return sum(1 for r in abstained if not r.correct) / float(len(abstained))

    def answered_error_rate(self):
        answered = [r for r in self.records if not r.abstained]
        if not answered:
            return None
        return sum(1 for r in answered if not r.correct) / float(len(answered))

    def mean_confidence(self, answered_only=False):
        pool = [r for r in self.records if not r.abstained] if answered_only \
            else self.records
        if not pool:
            return None
        return sum(r.confidence for r in pool) / float(len(pool))

    def to_dict(self):
        return {"meta": self.meta,
                "records": [r.to_dict() for r in self.records]}

    @classmethod
    def from_dict(cls, payload):
        return cls([Record.from_dict(r) for r in payload["records"]],
                   meta=payload.get("meta"))

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, text):
        return cls.from_dict(json.loads(text))
