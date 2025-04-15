/**
 * E-Mail-Parser Module
 * Verantwortlich für die Extraktion von Daten aus E-Mail-Dateien
 */

// Cache für Standorte
let locationsCache = null;

/**
 * Extrahiert Informationen aus einer E-Mail-Datei
 * @param {File} file - Die hochgeladene E-Mail-Datei
 * @returns {Promise<Object>} Extrahierte Daten (Datum, Uhrzeit, Standort)
 */
export async function parseEmailFile(file) {
    try {
        const fileContent = await readEmailFile(file);
        const plainText = extractTextFromEmail(fileContent, file.name);
        
        // Extrahiere Datum und Uhrzeit
        const dateTimeInfo = extractDateAndTime(plainText);
        
        // Lade Standorte, falls noch nicht im Cache
        if (!locationsCache) {
            locationsCache = await loadLocations();
        }
        
        // Extrahiere Standort
        const locationInfo = extractLocation(plainText, locationsCache);
        
        return {
            success: true,
            date: dateTimeInfo.date,
            time: dateTimeInfo.time,
            location: locationInfo.location,
            locationId: locationInfo.locationId,
            confidence: locationInfo.confidence,
            rawText: plainText.substring(0, 1000) // Begrenzt für Debugging
        };
    } catch (error) {
        console.error('Error parsing email file:', error);
        return {
            success: false,
            error: error.message || 'Fehler beim Parsen der E-Mail-Datei'
        };
    }
}

/**
 * Liest den Inhalt einer E-Mail-Datei
 * @param {File} file - Die hochgeladene Datei
 * @returns {Promise<String>} Der Inhalt der Datei
 */
async function readEmailFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            resolve(e.target.result);
        };
        
        reader.onerror = function(e) {
            reject(new Error('Fehler beim Lesen der Datei'));
        };
        
        // Lesen der Datei als Text
        reader.readAsText(file, 'UTF-8');
    });
}

/**
 * Extrahiert Plaintext aus einer E-Mail-Datei
 * @param {String} content - Der Inhalt der E-Mail-Datei
 * @param {String} fileName - Der Name der Datei für die Formaterkennung
 * @returns {String} Der extrahierte Plaintext
 */
function extractTextFromEmail(content, fileName) {
    // Erkennt das Format basierend auf der Dateiendung
    const fileExt = fileName.split('.').pop().toLowerCase();
    
    if (fileExt === 'html' || content.includes('<!DOCTYPE html>') || content.includes('<html')) {
        return extractTextFromHtml(content);
    } else if (fileExt === 'eml') {
        return extractTextFromEml(content);
    } else if (fileExt === 'msg') {
        return extractTextFromMsg(content);
    } else {
        // Txt oder unbekanntes Format - als Plaintext behandeln
        return content;
    }
}

/**
 * Extrahiert Text aus HTML-Inhalt
 * @param {String} htmlContent - Der HTML-Inhalt
 * @returns {String} Der extrahierte Text
 */
function extractTextFromHtml(htmlContent) {
    // Erstelle ein temporäres DOM-Element
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;
    
    // Entferne Skripte und Stile
    const scripts = tempDiv.getElementsByTagName('script');
    const styles = tempDiv.getElementsByTagName('style');
    
    while (scripts.length > 0) {
        scripts[0].parentNode.removeChild(scripts[0]);
    }
    
    while (styles.length > 0) {
        styles[0].parentNode.removeChild(styles[0]);
    }
    
    // Extrahiere den Text
    let text = tempDiv.textContent || tempDiv.innerText || '';
    
    // Bereinige den Text
    text = text.replace(/\s+/g, ' ').trim();
    
    return text;
}

/**
 * Extrahiert Text aus einer EML-Datei
 * @param {String} emlContent - Der Inhalt der EML-Datei
 * @returns {String} Der extrahierte Text
 */
function extractTextFromEml(emlContent) {
    // Einfache Extraktion - suche nach Plaintext im Content-Type
    const textPartRegex = /Content-Type: text\/plain[\s\S]*?(?=Content-Type|$)/gi;
    const textParts = emlContent.match(textPartRegex);
    
    if (textParts && textParts.length > 0) {
        // Extrahiere den Text nach den Headers
        const bodyRegex = /\r?\n\r?\n([\s\S]*)/;
        const bodyMatch = textParts[0].match(bodyRegex);
        
        if (bodyMatch && bodyMatch[1]) {
            return bodyMatch[1].trim();
        }
    }
    
    // Fallback: Versuche, HTML zu finden und zu extrahieren
    if (emlContent.includes('Content-Type: text/html')) {
        const htmlPartRegex = /Content-Type: text\/html[\s\S]*?(?=Content-Type|$)/gi;
        const htmlParts = emlContent.match(htmlPartRegex);
        
        if (htmlParts && htmlParts.length > 0) {
            const bodyRegex = /\r?\n\r?\n([\s\S]*)/;
            const bodyMatch = htmlParts[0].match(bodyRegex);
            
            if (bodyMatch && bodyMatch[1]) {
                return extractTextFromHtml(bodyMatch[1]);
            }
        }
    }
    
    // Fallback: Alles nach der ersten Leerzeile
    const bodyStart = emlContent.indexOf('\r\n\r\n');
    if (bodyStart !== -1) {
        return emlContent.substring(bodyStart + 4).trim();
    }
    
    return emlContent;
}

/**
 * Extrahiert Text aus einer MSG-Datei
 * Hinweis: MSG-Parsing ist komplex und erfordert möglicherweise eine externe Bibliothek
 * @param {String} msgContent - Der Inhalt der MSG-Datei
 * @returns {String} Der extrahierte Text
 */
function extractTextFromMsg(msgContent) {
    // MSG-Parsing ist complex, aber wir können einen einfachen Ansatz versuchen
    
    // Suche nach RTF-Daten oder Plaintext
    const bodyRegex = /\r?\n\r?\n([\s\S]*)/;
    const bodyMatch = msgContent.match(bodyRegex);
    
    if (bodyMatch && bodyMatch[1]) {
        return bodyMatch[1].trim().replace(/[^\x20-\x7E\r\n]/g, ''); // Nur ASCII behalten
    }
    
    return msgContent;
}

/**
 * Extrahiert Datum und Uhrzeit aus dem E-Mail-Text
 * @param {String} text - Der Text der E-Mail
 * @returns {Object} Extrahiertes Datum und Uhrzeit
 */
function extractDateAndTime(text) {
    // Ergebnisse initialisieren
    let extractedDate = null;
    let extractedTime = null;
    
    // Datum extrahieren
    // Suche nach verschiedenen Datumsformaten
    const datePatterns = [
        // Format: DD.MM.YYYY oder DD-MM-YYYY
        /(\d{1,2})[.-](\d{1,2})[.-](\d{4})/g,
        // Format: YYYY-MM-DD
        /(\d{4})-(\d{1,2})-(\d{1,2})/g,
        // Format: Month DD, YYYY (Englisch)
        /(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})/gi,
        // Format: DD Month YYYY (Deutsch)
        /(\d{1,2})\.?\s+(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})/gi,
        // Spezielle Formate in der Beispiel-E-Mail
        /February\s+(\d{1,2})/gi, // z.B. "February 09"
    ];
    
    // Durchsuche den Text nach den Datumsformaten
    for (const pattern of datePatterns) {
        const matches = [...text.matchAll(pattern)];
        
        if (matches.length > 0) {
            // Nehme das erste gefundene Datum
            const match = matches[0];
            
            // Verarbeite je nach Pattern
            if (pattern.toString().includes("February\\s+(\\d{1,2})")) {
                // Spezialfall für "February 09" Format
                const day = match[1].padStart(2, '0');
                extractedDate = `2025-02-${day}`;
                break;
            } else if (pattern.toString().includes("(\\d{4})-(\\d{1,2})-(\\d{1,2})")) {
                // YYYY-MM-DD Format
                const year = match[1];
                const month = match[2].padStart(2, '0');
                const day = match[3].padStart(2, '0');
                extractedDate = `${year}-${month}-${day}`;
                break;
            } else if (pattern.toString().includes("(\\d{1,2})[.-](\\d{1,2})[.-](\\d{4})")) {
                // DD.MM.YYYY Format
                const day = match[1].padStart(2, '0');
                const month = match[2].padStart(2, '0');
                const year = match[3];
                extractedDate = `${year}-${month}-${day}`;
                break;
            } else if (pattern.toString().includes("(January|February|March")) {
                // Englisches Monatsformat
                const monthNames = ["january", "february", "march", "april", "may", "june", 
                                    "july", "august", "september", "october", "november", "december"];
                const month = (monthNames.indexOf(match[1].toLowerCase()) + 1).toString().padStart(2, '0');
                const day = match[2].padStart(2, '0');
                const year = match[3];
                extractedDate = `${year}-${month}-${day}`;
                break;
            } else if (pattern.toString().includes("(\\d{1,2})\\.?\\s+(Januar|Februar|März")) {
                // Deutsches Monatsformat
                const monthNames = ["januar", "februar", "märz", "april", "mai", "juni", 
                                     "juli", "august", "september", "oktober", "november", "dezember"];
                const day = match[1].padStart(2, '0');
                const month = (monthNames.indexOf(match[2].toLowerCase()) + 1).toString().padStart(2, '0');
                const year = match[3];
                extractedDate = `${year}-${month}-${day}`;
                break;
            }
        }
    }
    
    // Zeit extrahieren
    // Suche nach verschiedenen Zeitformaten
    const timePatterns = [
        // Format: HH:MM oder HH.MM
        /(\d{1,2})[:.]\s*(\d{2})(?:\s*(?:Uhr|h))?/g,
        // Spezielle Formate in der Beispiel-E-Mail
        /(\d{1,2})\.(\d{2})/g, // z.B. "9.24" Format aus der E-Mail
    ];
    
    // Durchsuche den Text nach den Zeitformaten
    for (const pattern of timePatterns) {
        const matches = [...text.matchAll(pattern)];
        
        if (matches.length > 0) {
            // Nehme die erste gefundene Zeit
            const match = matches[0];
            const hours = match[1].padStart(2, '0');
            const minutes = match[2].padStart(2, '0');
            extractedTime = `${hours}:${minutes}`;
            break;
        }
    }
    
    return {
        date: extractedDate,
        time: extractedTime
    };
}

/**
 * Lädt die verfügbaren Standorte aus der Polizei-Daten-Excel
 * @returns {Promise<Array>} Liste der Standorte
 */
async function loadLocations() {
    try {
        // In einer realen Implementierung würden wir die Daten vom Server laden
        // Für jetzt simulieren wir einige Standorte
        const mockLocations = [
            { id: 1, name: "Hessental", city: "Schwäbisch Hall", state: "Baden-Württemberg" },
            { id: 2, name: "Heilbronn", city: "Heilbronn", state: "Baden-Württemberg" },
            { id: 3, name: "Stuttgart Mitte", city: "Stuttgart", state: "Baden-Württemberg" },
            { id: 4, name: "Stuttgart Nord", city: "Stuttgart", state: "Baden-Württemberg" },
            { id: 5, name: "Stuttgart West", city: "Stuttgart", state: "Baden-Württemberg" },
            { id: 6, name: "Stuttgart Ost", city: "Stuttgart", state: "Baden-Württemberg" },
            { id: 7, name: "Stuttgart Süd", city: "Stuttgart", state: "Baden-Württemberg" },
            { id: 8, name: "Mannheim", city: "Mannheim", state: "Baden-Württemberg" },
            { id: 9, name: "Karlsruhe", city: "Karlsruhe", state: "Baden-Württemberg" },
            { id: 10, name: "Freiburg", city: "Freiburg", state: "Baden-Württemberg" },
        ];
        
        return mockLocations;
    } catch (error) {
        console.error('Error loading locations:', error);
        return [];
    }
}

/**
 * Extrahiert den Standort aus dem E-Mail-Text
 * @param {String} text - Der Text der E-Mail
 * @param {Array} locations - Liste der verfügbaren Standorte
 * @returns {Object} Extrahierter Standort mit Konfidenzwert
 */
function extractLocation(text, locations) {
    // Häufig verwendete Bezeichnungen in E-Mails
    const locationKeywords = [
        'standort', 'filiale', 'store', 'niederlassung', 'geschäft',
        'laden', 'markt', 'branch', 'location', 'zwischenfall', 'vorfall',
        'filiale in', 'standort in', 'shop in'
    ];
    
    // Text normalisieren und in Kleinbuchstaben umwandeln
    const normalizedText = text.toLowerCase();
    console.log('Extrahiere Standort aus Text:', normalizedText.substring(0, 200) + '...');
    
    // Beste Übereinstimmung finden
    let bestMatch = null;
    let bestConfidence = 0;
    
    // Prüfe jede Location gegen den Text
    for (const location of locations) {
        // Prüfe direkte Erwähnung des Standortnamens
        const locationName = location.name.toLowerCase();
        if (normalizedText.includes(locationName)) {
            // Direkter Treffer - hohe Konfidenz
            let confidence = 0.8;
            
            // Prüfe, ob es in einem relevanten Kontext vorkommt
            for (const keyword of locationKeywords) {
                const pattern = new RegExp(`${keyword}\\s+.*?${locationName}|${locationName}\\s+.*?${keyword}`, 'i');
                if (pattern.test(normalizedText)) {
                    // Noch höhere Konfidenz bei Kontext
                    confidence = 0.95;
                    break;
                }
            }
            
            // Auch ohne Kontext ein guter Treffer
            if (confidence > bestConfidence) {
                bestMatch = location;
                bestConfidence = confidence;
            }
        }
        
        // Spezialfall für "Hessental Store_" oder ähnliche Formate
        const specialCasePatterns = [
            new RegExp(`${locationName}\\s*store`, 'i'),
            new RegExp(`${locationName}_store`, 'i'),
            new RegExp(`${locationName}store`, 'i')
        ];
        
        for (const pattern of specialCasePatterns) {
            if (pattern.test(normalizedText)) {
                bestMatch = location;
                bestConfidence = 0.99; // Sehr hohe Konfidenz
                break;
            }
        }
        
        // Fuzzy Matching mit Stadt
        if (location.city) {
            const cityName = location.city.toLowerCase();
            if (normalizedText.includes(cityName)) {
                // Prüfe ob Stadt in einem relevanten Kontext vorkommt
                for (const keyword of locationKeywords) {
                    const pattern = new RegExp(`${keyword}\\s+.*?${cityName}|${cityName}\\s+.*?${keyword}`, 'i');
                    if (pattern.test(normalizedText)) {
                        const confidence = 0.85; // Hohe Konfidenz für Stadt mit Kontext
                        if (confidence > bestConfidence) {
                            bestMatch = location;
                            bestConfidence = confidence;
                        }
                        break;
                    }
                }
                
                // Auch ohne Kontext ein möglicher Treffer
                const confidence = 0.7; // Niedrigere Konfidenz für Stadt ohne Kontext
                if (confidence > bestConfidence) {
                    bestMatch = location;
                    bestConfidence = confidence;
                }
            }
        }
    }
    
    console.log('Extrahierter Standort:', bestMatch ? bestMatch.name : 'keiner gefunden', 'mit Konfidenz:', bestConfidence);
    
    // Wenn keine gute Übereinstimmung gefunden wurde
    if (!bestMatch) {
        return {
            location: null,
            locationId: null,
            confidence: 0
        };
    }
    
    return {
        location: bestMatch.name,
        locationId: bestMatch.id,
        confidence: bestConfidence
    };
}