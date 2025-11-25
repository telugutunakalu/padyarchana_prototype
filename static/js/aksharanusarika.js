/**
 * Aksharanusarika v0.0.6a - Telugu Text Analysis Library
 * Extracted from aksharanusarika.html for integration with Padyarchana
 */

//////////////////////////////////////////////////////////////////////////
// LINGUISTIC DATA AND CONSTANTS
//////////////////////////////////////////////////////////////////////////
const dependentToIndependent = {
    "ా": "ఆ", "ి": "ఇ", "ీ": "ఈ", "ు": "ఉ", "ూ": "ఊ", "ృ": "ఋ",
    "ౄ": "ౠ", "ె": "ఎ", "ే": "ఏ", "ై": "ఐ", "ొ": "ఒ", "ో": "ఓ", "ౌ": "ఔ"
};
const halant = "్";
const teluguConsonants = new Set([
    "క", "ఖ", "గ", "ఘ", "ఙ", "చ", "ఛ", "జ", "ఝ", "ఞ", "ట", "ఠ", "డ", "ఢ", "ణ",
    "త", "థ", "ద", "ధ", "న", "ప", "ఫ", "బ", "భ", "మ", "య", "ర", "ల", "వ",
    "శ", "ష", "స", "హ", "ళ", "ఱ"
]);
const longVowels = new Set(["ా", "ీ", "ూ", "ే", "ో", "ౌ", "ౄ"]);
const independentVowels = new Set([
    "అ", "ఆ", "ఇ", "ఈ", "ఉ", "ఊ", "ఋ", "ౠ", "ఎ", "ఏ", "ఐ", "ఒ", "ఓ", "ఔ"
]);
const diacritics = new Set(["ం", "ః"]);
const dependentVowels = new Set(Object.keys(dependentToIndependent));
const ignorable_chars = new Set([' ', '\n', 'ఁ', '​']);

const PLUTAMULU = new Set(["ఐ", "ఔ"]);
const SARALAMULU = new Set(["గ", "జ", "డ", "ద", "బ"]);
const PARUSHAMULU = new Set(["క", "చ", "ట", "త", "ప"]);
const STHIRAMULU = new Set([
    "ఖ", "ఘ", "ఙ", "ఛ", "ఝ", "ఞ", "ఠ", "ఢ", "ణ", "థ", "ధ", "న",
    "ఫ", "భ", "మ", "య", "ర", "ఱ", "ల", "ళ", "వ", "శ", "ష", "స", "హ"
]);
const KA_VARGAMU = new Set(["క", "ఖ", "గ", "ఘ", "ఙ"]);
const CHA_VARGAMU = new Set(["చ", "ౘ", "ఛ", "జ", "ౙ", "ఝ", "ఞ"]);
const TA_VARGAMU = new Set(["ట", "ఠ", "డ", "ఢ", "ణ"]);
const THA_VARGAMU = new Set(["త", "థ", "ద", "ధ", "న"]);
const PA_VARGAMU = new Set(["ప", "ఫ", "బ", "భ", "మ"]);
const SPARSHA_MULU = new Set([...KA_VARGAMU, ...CHA_VARGAMU, ...TA_VARGAMU, ...THA_VARGAMU, ...PA_VARGAMU]);
const OOSHMA_MULU = new Set(["శ", "స", "ష", "హ"]);
const ANTASTA_MULU = new Set(["య", "ర", "ఱ", "ల", "ళ", "వ"]);
const KANTHYAMULU = new Set(["అ", "ఆ", "క", "ఖ", "గ", "ఘ", "ఙ", "హ"]);
const TAALAVYAMULU = new Set(["ఇ", "ఈ", "చ", "ఛ", "జ", "ఝ", "య", "శ"]);
const MOORDHANYAMULU = new Set(["ఋ", "ౠ", "ట", "ఠ", "డ", "ఢ", "ణ", "ష", "ఱ", "ర"]);
const DANTYAMULU = new Set(["ఌ", "ౡ", "త", "థ", "ద", "ధ", "ౘ", "ౙ", "ల", "స"]);
const OOSHTYAMULU = new Set(["ఉ", "ఊ", "ప", "ఫ", "బ", "భ", "మ"]);
const ANUNAASIKA_MULU = new Set(["ఙ", "ఞ", "ణ", "న", "మ"]);
const KANTHATAALAVYA_MULU = new Set(["ఎ", "ఏ", "ఐ"]);
const KANTHOSH_TYAMULU = new Set(["ఒ", "ఓ", "ఔ"]);
const DANTYOSH_TYAMULU = new Set(["వ"]);

const GANA_DEFINITIONS = {
    "Ekaakshara Ganas (1-Syllable)": {"U": "Guru", "I": "Laghu"},
    "Rendakshara Ganas (2-Syllable)": {"II": "Lalamu", "IU": "Lagamu (Va)", "UI": "Galamu (Ha)", "UU": "Gagamu"},
    "Moodakshara Ganas (3-Syllable)": {"IUU": "Ya", "UUU": "Ma", "UUI": "Ta", "UIU": "Ra", "IUI": "Ja", "UII": "Bha", "III": "Na", "IIU": "Sa"},
    "Surya Ganas": {"III": "Na", "UI": "Ha"},
    "Indra Ganas": {"IIIU": "Naga", "IIUI": "Sala", "IIII": "Nala", "UII": "Bha", "UIU": "Ra", "UUI": "Ta"},
    "Chandra Ganas": {"UIII": "Bhala", "UIIU": "Bhagaru", "UUII": "Tala", "UUIU": "Taga", "UUUI": "Malagha", "IIIII": "Nalala", "IIIUU": "Nagaga", "IIIIU": "Nava", "IIUUI": "Saha", "IIUIU": "Sava", "IIUUU": "Sagaga", "IIIUI": "Naha", "UIUU": "Raguru", "IIII": "Nala"}
};

//////////////////////////////////////////////////////////////////////////
// UTILITY FUNCTIONS
//////////////////////////////////////////////////////////////////////////

function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const chr = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0;
    }
    return 'id-' + (hash >>> 0).toString(16);
}

function addLetterCategories(ch, categories) {
    if (PLUTAMULU.has(ch)) categories.add("ప్లుతములు");
    if (SARALAMULU.has(ch)) categories.add("సరళములు");
    if (PARUSHAMULU.has(ch)) categories.add("పరుషములు");
    if (STHIRAMULU.has(ch)) categories.add("స్థిరములు");
    if (KA_VARGAMU.has(ch)) categories.add("క వర్గము");
    if (CHA_VARGAMU.has(ch)) categories.add("చ వర్గము");
    if (TA_VARGAMU.has(ch)) categories.add("ట వర్గము");
    if (THA_VARGAMU.has(ch)) categories.add("త వర్గము");
    if (PA_VARGAMU.has(ch)) categories.add("ప వర్గము");
    if (SPARSHA_MULU.has(ch)) categories.add("స్పర్శములు");
    if (OOSHMA_MULU.has(ch)) categories.add("ఊష్మాలు");
    if (ANTASTA_MULU.has(ch)) categories.add("అంతస్తములు");
    if (KANTHYAMULU.has(ch)) categories.add("కంఠ్యములు");
    if (TAALAVYAMULU.has(ch)) categories.add("తాలవ్యములు");
    if (MOORDHANYAMULU.has(ch)) categories.add("మూర్ధన్యములు");
    if (DANTYAMULU.has(ch)) categories.add("దంత్యములు");
    if (OOSHTYAMULU.has(ch)) categories.add("ఓష్ఠ్యములు");
    if (ANUNAASIKA_MULU.has(ch)) categories.add("అనునాసికములు");
    if (KANTHATAALAVYA_MULU.has(ch)) categories.add("కంఠతాలవ్యములు");
    if (KANTHOSH_TYAMULU.has(ch)) categories.add("కంఠోష్ఠ్యములు");
    if (DANTYOSH_TYAMULU.has(ch)) categories.add("దంత్యోష్ఠ్యములు");
}

function categorizeAksharam(aksharam) {
    const categories = new Set();
    const independentLongVowels = new Set(["ఆ", "ఈ", "ఊ", "ౠ", "ఏ", "ఓ"]);

    if (independentVowels.has(aksharam[0])) categories.add("అచ్చు");
    else if (diacritics.has(aksharam)) categories.add("అచ్చు");

    if ([...aksharam].some(c => teluguConsonants.has(c))) categories.add("హల్లు");

    if ([...aksharam].some(c => longVowels.has(c)) || independentLongVowels.has(aksharam)) {
        categories.add("దీర్ఘ");
    }

    if (aksharam.includes("ః")) categories.add("విసర్గ అక్షరం");
    if (aksharam.includes("ం")) categories.add("అనుస్వారం");

    let foundConjunct = false, foundDouble = false;
    for (let i = 0; i < aksharam.length - 2; i++) {
        if (teluguConsonants.has(aksharam[i]) && aksharam[i+1] === halant && teluguConsonants.has(aksharam[i+2])) {
            if (aksharam[i] === aksharam[i+2]) foundDouble = true;
            else foundConjunct = true;
        }
    }
    if (foundConjunct) categories.add("సంయుక్తాక్షరం");
    if (foundDouble) categories.add("ద్విత్వాక్షరం");

    if ((categories.has("హల్లు") || categories.has("అచ్చు")) && !categories.has("దీర్ఘ") && !categories.has("అనుస్వారం") && !categories.has("విసర్గ అక్షరం")) {
        categories.add("హ్రస్వాక్షరం");
    }

    for (const ch of aksharam) addLetterCategories(ch, categories);

    let foundDependentVowel = false;
    for (const dvSign in dependentToIndependent) {
        if (aksharam.includes(dvSign)) {
            foundDependentVowel = true;
            addLetterCategories(dependentToIndependent[dvSign], categories);
        }
    }

    if ([...aksharam].some(c => teluguConsonants.has(c)) && !foundDependentVowel && !aksharam.endsWith(halant)) {
         addLetterCategories("అ", categories);
    }

    return Array.from(categories).sort();
}

function splitAksharalu(word) {
    const coarseSplit = [];
    let i = 0;
    while (i < word.length) {
        if (ignorable_chars.has(word[i])) {
            coarseSplit.push(word[i]);
            i++;
            continue;
        }
        let current = "";
        if (teluguConsonants.has(word[i])) {
            current += word[i++];
            while (i < word.length && word[i] === halant) {
                current += word[i++];
                if (i < word.length && teluguConsonants.has(word[i])) {
                    current += word[i++];
                } else break;
            }
            while (i < word.length && (dependentVowels.has(word[i]) || diacritics.has(word[i]))) {
                current += word[i++];
            }
        } else {
            let char = word[i++];
            current += char;
            if (independentVowels.has(char) && i < word.length && diacritics.has(word[i])) {
                current += word[i++];
            }
        }
        coarseSplit.push(current);
    }

    if (coarseSplit.length === 0) return [];
    const finalAksharalu = [];
    for (const chunk of coarseSplit) {
        const isPolluHallu = chunk.length === 2 && teluguConsonants.has(chunk[0]) && chunk[1] === halant;
        if (isPolluHallu && finalAksharalu.length > 0 && !ignorable_chars.has(finalAksharalu[finalAksharalu.length - 1])) {
            finalAksharalu[finalAksharalu.length - 1] += chunk;
        } else {
            finalAksharalu.push(chunk);
        }
    }
    return finalAksharalu.filter(ak => ak);
}

function aksharaGanaVibhajana(aksharaluList) {
    if (!aksharaluList || aksharaluList.length === 0) return [];

    const ganamMarkers = new Array(aksharaluList.length).fill(null);

    for (let i = 0; i < aksharaluList.length; i++) {
        const aksharam = aksharaluList[i];
        if (ignorable_chars.has(aksharam)) {
            ganamMarkers[i] = "";
            continue;
        }

        ganamMarkers[i] = "I"; // Default to Laghu
        const tags = new Set(categorizeAksharam(aksharam));

        let isGuru = false;
        if (tags.has('దీర్ఘ')) isGuru = true;
        if (aksharam.includes('ఐ') || aksharam.includes('ఔ') || aksharam.includes('ై') || aksharam.includes('ౌ')) isGuru = true;
        if (tags.has('అనుస్వారం') || tags.has('విసర్గ అక్షరం')) isGuru = true;
        if (aksharam.endsWith(halant)) isGuru = true;
        if (isGuru) ganamMarkers[i] = "U";
    }

    for (let i = 0; i < aksharaluList.length; i++) {
        if (ganamMarkers[i] === "") continue;

        let nextSyllableIndex = -1;
        for (let j = i + 1; j < aksharaluList.length; j++) {
            if (!ignorable_chars.has(aksharaluList[j])) {
                nextSyllableIndex = j;
                break;
            }
        }

        if (nextSyllableIndex !== -1) {
            const nextAksharamTags = new Set(categorizeAksharam(aksharaluList[nextSyllableIndex]));
            if (nextAksharamTags.has('సంయుక్తాక్షరం') || nextAksharamTags.has('ద్విత్వాక్షరం')) {
                ganamMarkers[i] = "U";
            }
        }
    }
    return ganamMarkers;
}

//////////////////////////////////////////////////////////////////////////
// GANA ANALYZER CLASS
//////////////////////////////////////////////////////////////////////////

class GanaAnalyzer {
    constructor(definitions) {
        this.definitions = definitions;
        this.flatGanas = this._flattenDefinitions(definitions);
        this.memo = {};
    }

    _flattenDefinitions(definitions) {
        const flatMap = {};
        for (const category in definitions) {
            for (const pattern in definitions[category]) {
                flatMap[pattern] = definitions[category][pattern];
            }
        }
        return flatMap;
    }

    findSequentialCombinations(syllables, maxCombinations = 100) {
        this.memo = {}; // Reset memo for each new analysis
        this.maxCombinations = maxCombinations;
        this.foundCombinations = 0;

        // Limit syllable length to prevent exponential explosion
        const MAX_SYLLABLES = 30;
        if (syllables.length > MAX_SYLLABLES) {
            console.warn(`Syllable count (${syllables.length}) exceeds maximum (${MAX_SYLLABLES}). Truncating for analysis.`);
            syllables = syllables.slice(0, MAX_SYLLABLES);
        }

        return this._findCombinationsRecursiveMemoized(syllables);
    }

    _findCombinationsRecursiveMemoized(remainingSyllables) {
        // Early termination if we've found enough combinations
        if (this.foundCombinations >= this.maxCombinations) {
            return [];
        }

        const key = remainingSyllables.join(',');
        if (key in this.memo) {
            return this.memo[key];
        }
        if (remainingSyllables.length === 0) {
            this.foundCombinations++;
            return [[]];
        }

        const allPossiblePartitions = [];
        for (let i = 1; i <= remainingSyllables.length; i++) {
            // Early termination check
            if (this.foundCombinations >= this.maxCombinations) {
                break;
            }

            const prefix = remainingSyllables.slice(0, i).join('');
            if (prefix in this.flatGanas) {
                const ganaInfo = { name: this.flatGanas[prefix], pattern: prefix };
                const suffix = remainingSyllables.slice(i);
                const suffixCombinations = this._findCombinationsRecursiveMemoized(suffix);
                for (const combo of suffixCombinations) {
                    if (this.foundCombinations >= this.maxCombinations) {
                        break;
                    }
                    allPossiblePartitions.push([ganaInfo, ...combo]);
                }
            }
        }
        this.memo[key] = allPossiblePartitions;
        return allPossiblePartitions;
    }
}

function mapSyllablesToPartition(partition, syllables) {
    const mappedPartition = [];
    let syllableIndex = 0;
    for (const gana of partition) {
        const patternLen = gana.pattern.length;
        const syllableSlice = syllables.slice(syllableIndex, syllableIndex + patternLen);
        const syllableText = syllableSlice.join('');

        mappedPartition.push({
            syllable_text: syllableText,
            name: gana.name,
            pattern: gana.pattern
        });
        syllableIndex += patternLen;
    }
    return mappedPartition;
}

//////////////////////////////////////////////////////////////////////////
// MAIN ANALYSIS FUNCTIONS
//////////////////////////////////////////////////////////////////////////

function analyzeTeluguWord(word) {
    const sanitized = word.replace(/[^\u0C00-\u0C7F\s\u0C01\u200B]+/g, "");
    const aksharaluList = splitAksharalu(sanitized);
    const analysis = {};
    const categoryCounts = {};
    let allTags = new Set();

    for (const aksharam of aksharaluList) {
        if (ignorable_chars.has(aksharam)) continue;
        const tags = categorizeAksharam(aksharam);
        const key = aksharam;
        if (!analysis[key]) {
            analysis[key] = { tags, count: 0 };
        }
        analysis[key].count++;
    }

    for (const key in analysis) {
        const info = analysis[key];
        for (const cat of info.tags) {
            categoryCounts[cat] = (categoryCounts[cat] || 0) + info.count;
            allTags.add(cat);
        }
    }

    return {
        word: sanitized,
        uniqueId: simpleHash(sanitized),
        aksharalu: Object.entries(analysis).map(([aksharam, data]) => ({ aksharam, ...data })),
        aksharaluList,
        categoryCounts,
        tags: allTags
    };
}

function calculateLinguisticStatistics(analysis) {
    const categoryCounts = analysis.categoryCounts;
    const pureAksharalu = analysis.aksharaluList.filter(ak => !ignorable_chars.has(ak));

    const vowelCount = categoryCounts["అచ్చు"] || 0;
    const consonantCount = categoryCounts["హల్లు"] || 0;
    const longVowelCount = categoryCounts["దీర్ఘ"] || 0;
    const shortVowelCount = categoryCounts["హ్రస్వాక్షరం"] || 0;
    const conjunctCount = categoryCounts["సంయుక్తాక్షరం"] || 0;
    const doubletCount = categoryCounts["ద్విత్వాక్షరం"] || 0;
    const anusvaaramCount = categoryCounts["అనుస్వారం"] || 0;
    const visargaCount = categoryCounts["విసర్గ అక్షరం"] || 0;

    const totalAksharas = pureAksharalu.length;
    const uniqueAksharas = analysis.aksharalu.length;

    return {
        totalAksharas,
        uniqueAksharas,
        vowelCount,
        consonantCount,
        vowelToConsonantRatio: consonantCount > 0 ? (vowelCount / consonantCount).toFixed(3) : 0,
        longVowelCount,
        shortVowelCount,
        conjunctCount,
        doubletCount,
        anusvaaramCount,
        visargaCount,
        complexityScore: totalAksharas > 0 ? ((conjunctCount + doubletCount) / totalAksharas * 100).toFixed(2) : 0
    };
}

function calculateProsodyStatistics(ganaMarkers, ganaCombinations) {
    const pureGanas = ganaMarkers.filter(m => m !== "");

    if (pureGanas.length === 0) {
        return {
            totalSyllables: 0,
            guruCount: 0,
            laghuCount: 0,
            guruToLaghuRatio: 0,
            guruPercentage: 0,
            laghuPercentage: 0,
            mostCommonGana: null,
            ganaVariety: 0
        };
    }

    const guruCount = pureGanas.filter(m => m === 'U').length;
    const laghuCount = pureGanas.filter(m => m === 'I').length;
    const totalSyllables = pureGanas.length;

    // Find most common gana pattern
    let mostCommonGana = null;
    let ganaVariety = 0;

    if (ganaCombinations && ganaCombinations.length > 0) {
        const ganaNames = {};
        ganaCombinations.forEach(combo => {
            combo.forEach(gana => {
                const name = gana.name;
                ganaNames[name] = (ganaNames[name] || 0) + 1;
            });
        });

        if (Object.keys(ganaNames).length > 0) {
            mostCommonGana = Object.entries(ganaNames).sort((a, b) => b[1] - a[1])[0][0];
            ganaVariety = Object.keys(ganaNames).length;
        }
    }

    return {
        totalSyllables,
        guruCount,
        laghuCount,
        guruToLaghuRatio: laghuCount > 0 ? (guruCount / laghuCount).toFixed(3) : 0,
        guruPercentage: (guruCount / totalSyllables * 100).toFixed(2),
        laghuPercentage: (laghuCount / totalSyllables * 100).toFixed(2),
        mostCommonGana,
        ganaVariety
    };
}

function calculateVargamDistribution(categoryCounts) {
    return {
        "క వర్గము": categoryCounts["క వర్గము"] || 0,
        "చ వర్గము": categoryCounts["చ వర్గము"] || 0,
        "ట వర్గము": categoryCounts["ట వర్గము"] || 0,
        "త వర్గము": categoryCounts["త వర్గము"] || 0,
        "ప వర్గము": categoryCounts["ప వర్గము"] || 0
    };
}

function calculateArticulationDistribution(categoryCounts) {
    return {
        "కంఠ్యములు": categoryCounts["కంఠ్యములు"] || 0,
        "తాలవ్యములు": categoryCounts["తాలవ్యములు"] || 0,
        "మూర్ధన్యములు": categoryCounts["మూర్ధన్యములు"] || 0,
        "దంత్యములు": categoryCounts["దంత్యములు"] || 0,
        "ఓష్ఠ్యములు": categoryCounts["ఓష్ఠ్యములు"] || 0,
        "కంఠతాలవ్యములు": categoryCounts["కంఠతాలవ్యములు"] || 0,
        "కంఠోష్ఠ్యములు": categoryCounts["కంఠోష్ఠ్యములు"] || 0,
        "దంత్యోష్ఠ్యములు": categoryCounts["దంత్యోష్ఠ్యములు"] || 0
    };
}

function calculatePhoneticsDistribution(categoryCounts) {
    return {
        "స్పర్శములు": categoryCounts["స్పర్శములు"] || 0,
        "ఊష్మాలు": categoryCounts["ఊష్మాలు"] || 0,
        "అంతస్తములు": categoryCounts["అంతస్తములు"] || 0,
        "అనునాసికములు": categoryCounts["అనునాసికములు"] || 0
    };
}

function calculateVyanjanaClassification(categoryCounts) {
    return {
        "సరళములు": categoryCounts["సరళములు"] || 0,
        "పరుషములు": categoryCounts["పరుషములు"] || 0,
        "స్థిరములు": categoryCounts["స్థిరములు"] || 0
    };
}

/**
 * Main function to analyze Telugu text and return comprehensive analysis
 * @param {string} text - Telugu text to analyze
 * @returns {object} - Comprehensive analysis results
 */
function analyzeTeluguText(text) {
    const startTime = performance.now();

    // Sanitize input
    const sanitized = text.replace(/[^\u0C00-\u0C7F\s\u0C01\u200B\n]+/g, "");

    // Perform core analysis
    const analysis = analyzeTeluguWord(sanitized);
    const ganaMarkers = aksharaGanaVibhajana(analysis.aksharaluList);

    // Gana marker details - map ALL aksharas with their markers
    // ganaMarkers array has same length as aksharaluList
    const ganaMarkerDetails = analysis.aksharaluList.map((aksharam, idx) => {
        const marker = ganaMarkers[idx] || '';
        const isIgnorable = ignorable_chars.has(aksharam);

        return {
            aksharam,
            marker: marker || '-',  // Use '-' to indicate no gana marker
            position: idx,
            isIgnorable: isIgnorable
        };
    });

    // Gana combinations analysis
    const pureGanas = ganaMarkers.filter(m => m !== "");
    const pureAksharalu = analysis.aksharaluList.filter(ak => !ignorable_chars.has(ak));
    let ganaCombinationsList = [];
    const ganaAnalyzer = new GanaAnalyzer(GANA_DEFINITIONS);

    if (pureGanas.length > 0 && pureGanas.length <= 30) {
        try {
            const MAX_COMBINATIONS = 50;
            const combinations = ganaAnalyzer.findSequentialCombinations(pureGanas, MAX_COMBINATIONS);

            ganaCombinationsList = combinations.slice(0, MAX_COMBINATIONS).map(combo =>
                mapSyllablesToPartition(combo, pureAksharalu)
            );
        } catch (error) {
            console.error('Error finding gana combinations:', error);
            ganaCombinationsList = [];
        }
    } else if (pureGanas.length > 30) {
        console.warn(`Poem too long (${pureGanas.length} syllables) for gana combination analysis. Skipping.`);
    }

    // Calculate statistics
    const linguisticStats = calculateLinguisticStatistics(analysis);
    const prosodyStats = calculateProsodyStatistics(ganaMarkers, ganaCombinationsList);

    // Calculate category distributions
    const vargamDist = calculateVargamDistribution(analysis.categoryCounts);
    const articulationDist = calculateArticulationDistribution(analysis.categoryCounts);
    const phoneticsDist = calculatePhoneticsDistribution(analysis.categoryCounts);
    const vyanjanaClass = calculateVyanjanaClassification(analysis.categoryCounts);

    const processingTime = (performance.now() - startTime).toFixed(2);

    return {
        metadata: {
            inputHash: simpleHash(sanitized),
            processingTimeMs: parseFloat(processingTime)
        },
        input: {
            sanitizedText: sanitized
        },
        linguistic: {
            aksharalu: analysis.aksharalu,
            aksharaluList: analysis.aksharaluList,
            categoryCounts: analysis.categoryCounts,
            statistics: linguisticStats,
            distributions: {
                vargam: vargamDist,
                articulation: articulationDist,
                phonetics: phoneticsDist,
                vyanjanaClassification: vyanjanaClass
            }
        },
        prosody: {
            ganaSequence: pureGanas,
            ganaMarkers: ganaMarkerDetails,
            ganaCombinations: ganaCombinationsList,
            statistics: prosodyStats
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { analyzeTeluguText };
}
