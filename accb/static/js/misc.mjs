export const showMessage = (msg, options = {}) => {
    const notification = (options.notification !== undefined) ? options.notification : true;

    if (notification && Notification.permission === "granted")
        new Notification("ACCB Price Miner", { body: msg });

    Materialize.toast(msg, 8000, "rounded");
};

/**
 * Retorna um ratio de similaridade entre uma string s1 e s2
 * @param  {string} s1
 * @param  {string} s2
 */
export const similarity = (s1, s2) => {
    var longer = s1;
    var shorter = s2;
    if (s1.length < s2.length) {
        longer = s2;
        shorter = s1;
    }
    var longerLength = longer.length;
    if (longerLength == 0) {
        return 1.0;
    }
    return (longerLength - distance(longer, shorter)) / parseFloat(longerLength);
}

/**
 * Função de ajuda para a similarity, retorna a distancia entre as palavras.
 * @param  {string} s1
 * @param  {string} s2
 */
function distance(s1, s2) {
    s1 = s1.toLowerCase();
    s2 = s2.toLowerCase();

    var costs = new Array();
    for (var i = 0; i <= s1.length; i++) {
        var lastValue = i;
        for (var j = 0; j <= s2.length; j++) {
            if (i == 0)
                costs[j] = j;
            else {
                if (j > 0) {
                    var newValue = costs[j - 1];
                    if (s1.charAt(i - 1) != s2.charAt(j - 1))
                        newValue = Math.min(Math.min(newValue, lastValue),
                            costs[j]) + 1;
                    costs[j - 1] = lastValue;
                    lastValue = newValue;
                }
            }
        }
        if (i > 0)
            costs[s2.length] = lastValue;
    }
    return costs[s2.length];
}
