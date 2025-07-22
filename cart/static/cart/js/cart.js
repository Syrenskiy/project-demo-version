document.addEventListener('DOMContentLoaded', function () {
    const getCSRFToken = () => {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    };

    function updateCart(productId, action) {
        fetch(`/cart/add/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `quantity=1&override=${action === 'remove' ? 'true' : 'false'}`
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload(); // Перезагружаем страницу
                }
            })
            .catch(error => console.error('Ошибка:', error));
    }

    document.querySelectorAll('.increment').forEach(button => {
        button.addEventListener('click', function () {
            const productId = this.getAttribute('data-product-id');
            updateCart(productId, 'add');
        });
    });

    document.querySelectorAll('.decrement').forEach(button => {
        button.addEventListener('click', function () {
            const productId = this.getAttribute('data-product-id');
            updateCart(productId, 'remove');
        });
    });
});
