from datetime import date

# Fixed Lebanese public holidays (month, day) — repeat every year
FIXED_HOLIDAYS = [
    (1,  1),   # New Year's Day
    (1,  6),   # Armenian Orthodox Christmas
    (2,  9),   # St. Maroun's Day
    (2,  14),  # Rafik Hariri Memorial Day
    (3,  25),  # Feast of the Annunciation
    (5,  1),   # Labour Day
    (5,  25),  # Resistance and Liberation Day
    (8,  15),  # Assumption of the Virgin Mary
    (11, 22),  # Independence Day
    (12, 25),  # Christmas Day
]

# Variable religious holidays (lunar-based — must be updated each year)
VARIABLE_HOLIDAYS = {
    2025: [
        '2025-03-31', '2025-04-01',  # Eid al-Fitr
        '2025-04-18',                 # Good Friday
        '2025-04-20', '2025-04-21',  # Easter Sunday + Monday
        '2025-06-06', '2025-06-07',  # Eid al-Adha
        '2025-06-27',                 # Islamic New Year
        '2025-07-05',                 # Ashoura
        '2025-09-05',                 # Prophet's Birthday
    ],
    2026: [
        '2026-03-20', '2026-03-21',  # Eid al-Fitr
        '2026-04-03',                 # Good Friday (Western)
        '2026-04-05',                 # Easter Sunday (Western)
        '2026-04-10',                 # Good Friday (Orthodox)
        '2026-04-12',                 # Orthodox Easter Sunday
        '2026-05-28', '2026-05-29',  # Eid al-Adha
        '2026-06-16', '2026-06-17',  # Islamic New Year
        '2026-06-26',                 # Ashoura
        '2026-08-25', '2026-08-26',  # Prophet's Birthday
    ],
}


def get_lebanon_holidays(year):
    """Return a set of holiday date strings (YYYY-MM-DD) for the given year."""
    holidays = set()
    for month, day in FIXED_HOLIDAYS:
        holidays.add(date(year, month, day).strftime('%Y-%m-%d'))
    for d in VARIABLE_HOLIDAYS.get(year, []):
        holidays.add(d)
    return holidays
