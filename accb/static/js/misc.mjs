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
