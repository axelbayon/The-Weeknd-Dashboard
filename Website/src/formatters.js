/**
 * Module de formatage des nombres et valeurs en français
 */

/**
 * Formate un nombre avec séparateur de milliers (espace fine) et virgule décimale
 * @param {number} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales (défaut: 0)
 * @returns {string} - Nombre formaté (ex: "1 664 001" ou "3,52")
 */
function formatNumber(value, decimals = 0) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N.D.';
    }

    // Arrondir au nombre de décimales souhaité
    const rounded = Number(value.toFixed(decimals));
    
    // Séparer partie entière et décimale
    const parts = rounded.toString().split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1] || '';

    // Ajouter les espaces fines pour les milliers
    // Espace fine insécable : \u202F (ou espace normal pour compatibilité)
    const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '\u202F');

    // Retourner avec virgule décimale si nécessaire
    if (decimals > 0 && decimalPart) {
        return `${formattedInteger},${decimalPart.padEnd(decimals, '0')}`;
    }

    return formattedInteger;
}

/**
 * Formate un entier avec séparateur de milliers français (espace) - sans décimales
 * Utilise Intl.NumberFormat pour garantir la cohérence
 * @param {number} value - Entier à formater
 * @returns {string} - Nombre formaté (ex: "5 050 786 130", "68 403 452 747")
 */
function formatIntFr(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N.D.';
    }

    const formatter = new Intl.NumberFormat('fr-FR', {
        maximumFractionDigits: 0,
        useGrouping: true
    });

    return formatter.format(Number(value));
}

/**
 * Formate un pourcentage avec signe +/- et 2 décimales
 * @param {number|string} value - Valeur à formater (nombre ou "N.D.")
 * @returns {string} - Pourcentage formaté (ex: "+3,52 %", "-1,07 %", "N.D.")
 */
function formatPercent(value) {
    // Cas "Non mis-à-jour" : valeur 'N.D.' explicite, null, ou undefined
    if (value === 'N.D.' || value === null || value === undefined) {
        return 'Non mis-à-jour';
    }
    
    // Vérifier si c'est un nombre valide
    if (isNaN(value)) {
        return 'Non mis-à-jour';
    }

    const num = Number(value);
    
    // Cas spécial : 0 exact (pas de signe)
    if (num === 0) {
        return '0,00\u202F%';
    }
    
    // Utiliser Intl.NumberFormat avec signDisplay pour afficher +/- automatiquement
    const formatter = new Intl.NumberFormat('fr-FR', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        signDisplay: 'always' // Toujours afficher le signe pour les valeurs non-nulles
    });
    
    // Diviser par 100 car Intl.NumberFormat multiplie par 100 pour les pourcentages
    return formatter.format(num / 100);
}

/**
 * Formate un nombre de jours avec 2 décimales et suffixe "j"
 * @param {number|string} value - Nombre de jours (nombre ou "N.D.")
 * @returns {string} - Jours formatés (ex: "23,84 j", "N.D.")
 */
function formatDays(value) {
    if (value === 'N.D.' || value === null || value === undefined || isNaN(value)) {
        return 'N.D.';
    }

    const formatted = formatNumber(Number(value), 2);
    return `${formatted}\u202Fj`;
}

/**
 * Formate un palier en millions (M) ou milliards (B) avec virgule
 * @param {number} value - Valeur du palier
 * @returns {string} - Palier formaté (ex: "5,1 B", "300 M")
 */
function formatCap(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N.D.';
    }

    const num = Number(value);

    // Milliards (>= 1 000 000 000)
    if (num >= 1000000000) {
        const billions = num / 1000000000;
        // 1 décimale si pas un nombre entier, sinon 0 décimale
        const decimals = (billions % 1 === 0) ? 0 : 1;
        return `${formatNumber(billions, decimals)}\u202FB`;
    }

    // Millions (>= 1 000 000)
    if (num >= 1000000) {
        const millions = num / 1000000;
        // 1 décimale si pas un nombre entier, sinon 0 décimale
        const decimals = (millions % 1 === 0) ? 0 : 1;
        return `${formatNumber(millions, decimals)}\u202FM`;
    }

    // Moins d'un million : afficher tel quel
    return formatNumber(num, 0);
}

/**
 * Formate les streams totaux (grands nombres avec M/B)
 * @param {number} value - Nombre de streams
 * @returns {string} - Streams formatés (ex: "4,3 B", "156,2 M")
 */
function formatStreams(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N.D.';
    }

    const num = Number(value);

    // Milliards
    if (num >= 1000000000) {
        const billions = num / 1000000000;
        return `${formatNumber(billions, 1)}\u202FB`;
    }

    // Millions
    if (num >= 1000000) {
        const millions = num / 1000000;
        return `${formatNumber(millions, 1)}\u202FM`;
    }

    // Milliers
    if (num >= 1000) {
        const thousands = num / 1000;
        return `${formatNumber(thousands, 1)}\u202FK`;
    }

    return formatNumber(num, 0);
}

/**
 * Formate les streams quotidiens (nombres complets avec espaces)
 * @param {number} value - Nombre de streams quotidiens
 * @returns {string} - Streams formatés (ex: "5 300 000", "1 234 567")
 */
function formatDailyStreams(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N.D.';
    }

    return formatNumber(Number(value), 0);
}

// Tests unitaires inline (décommenter pour déboguer)
/*
console.log('=== Tests formatNumber ===');
console.log(formatNumber(1664001, 0)); // "1 664 001"
console.log(formatNumber(3.52, 2)); // "3,52"
console.log(formatNumber(1000000, 0)); // "1 000 000"

console.log('\n=== Tests formatPercent ===');
console.log(formatPercent(3.52)); // "+3,52 %"
console.log(formatPercent(-1.07)); // "-1,07 %"
console.log(formatPercent('N.D.')); // "N.D."
console.log(formatPercent(0)); // "0,00 %"

console.log('\n=== Tests formatDays ===');
console.log(formatDays(23.84)); // "23,84 j"
console.log(formatDays(1.5)); // "1,50 j"
console.log(formatDays('N.D.')); // "N.D."

console.log('\n=== Tests formatCap ===');
console.log(formatCap(5100000000)); // "5,1 B"
console.log(formatCap(2800000000)); // "2,8 B"
console.log(formatCap(300000000)); // "300 M"
console.log(formatCap(1000000000)); // "1 B"

console.log('\n=== Tests formatStreams ===');
console.log(formatStreams(4290300000)); // "4,3 B"
console.log(formatStreams(156200000)); // "156,2 M"
console.log(formatStreams(5300000)); // "5,3 M"
*/

// Export pour utilisation dans d'autres modules
window.formatters = {
    formatNumber,
    formatIntFr,
    formatPercent,
    formatDays,
    formatCap,
    formatStreams,
    formatDailyStreams
};
