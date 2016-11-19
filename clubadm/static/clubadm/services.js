(function(window, angular, undefined) {

  'use strict';

  var services = angular.module('clubadm.services', []);

  /**
   * Сервис для работы с текущим пользователем.
   *
   * Просто красивая обертка вокруг window.jsdata.
   */
  services.service('UserService', function() {
    /**
     * Возвращает информацию о текущем пользователе или null.
     */
    this.getCurrentUser = function() {
      return window.jsdata.user;
    };

    /**
     * Возвращает true, если пользователь аутентифицирован, иначе false.
     */
    this.isUserLoggedIn = function() {
      return window.jsdata.user !== null;
    };
  });

  /**
   * Сервис для всего остального :-)
   */
  services.service('SeasonService', ['$http', function($http) {
    /**
     * Получить самый последний сезон.
     */
    this.getLatest = function() {
      return $http.get('/seasons/latest');
    };

    /**
     * Получить информацию о сезоне по году проведения.
     */
    this.getByYear = function(year) {
      return $http.get('/seasons/' + year);
    };

    /**
     * Получить информацию об участнике.
     */
    this.getMemberByYear = function(year) {
      return $http.get('/seasons/' + year + '/member');
    };

    /**
     * Получить список сообщений из чата.
     */
    this.getMails = function(year) {
      return $http.get('/seasons/' + year + '/chat');
    };

    /**
     * Отправить сообщение.
     */
    this.sendMail = function(year, message, recipient) {
      return $http.post('/seasons/' + year + '/send_mail', {
        body: message,
        recipient: recipient,
      });
    };

    /**
     * Сообщить АПП, что подарок отправлен.
     */
    this.sendGift = function(year) {
        return $http.post('/seasons/' + year + '/send_gift');
    };

    /**
     * Сообщить АДМ, что подарок получен.
     */
    this.receiveGift = function(year) {
      return $http.post('/seasons/' + year + '/receive_gift');
    };

    /**
     * Записать пользователя в участники.
     */
    this.signUp = function(year, form) {
      return $http.post('/seasons/' + year + '/signup', form);
    };

    /**
     * Убрать пользователя из участников.
     */
    this.signOut = function(year) {
      return $http.post('/seasons/' + year + '/signout');
    };
  }]);

})(window, window.angular);
