$(function() {
    var reloadFragments = function() {
        $(".mdl-card").each(function(index, deployment) {
            var updated_url = fragmentURL.replace("1234",$(deployment).data("deployment"));
            $.get(updated_url, function(data) {
                $(deployment).html(data);
            });
        });
    };
    setInterval(reloadFragments, 10000);
});
